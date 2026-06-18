import json
import re
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from quasai.parser import count_items
from quasai.types import Requirements, Section, TestCase

_DEFAULT_MODEL = "phi4-mini"
_DEFAULT_URL = "http://ollama:11434"
_CHUNK_SIZE = 5

_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


@dataclass
class Chunk:
    prompt: str
    label: str
    item_count: int


class LLMProvider:
    async def generate(
        self,
        requirements: Requirements,
        progress: Callable[[str], None] | None = None,
    ) -> list[TestCase]:
        ...


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        base_url: str = _DEFAULT_URL,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")

    def _build_chunks(self, requirements: Requirements) -> list[Chunk]:
        chunks: list[Chunk] = []
        buffer_parts: list[str] = []
        buffer_count = 0
        buffer_label = requirements.title or "Требования"

        def flush(label: str) -> None:
            nonlocal buffer_parts, buffer_count
            if not buffer_parts:
                return
            prompt = "\n".join(buffer_parts)
            chunks.append(Chunk(prompt=prompt, label=label, item_count=buffer_count or 1))
            buffer_parts = []
            buffer_count = 0

        for section in requirements.sections:
            sec_text = section.content
            for sub in section.subsections:
                sec_text += "\n" + sub.content
            section_items = count_items(sec_text)
            if buffer_count + section_items > _CHUNK_SIZE and buffer_parts:
                flush(buffer_label)
            buffer_parts.append(f"{section.heading}\n{section.content}")
            for sub in section.subsections:
                buffer_parts.append(f"\n{sub.heading}\n{sub.content}")
            buffer_count += section_items
            buffer_label = section.heading

        flush(buffer_label)

        if not chunks:
            chunks.append(Chunk(
                prompt=f"Заголовок: {requirements.title}\n",
                label=requirements.title or "Требования",
                item_count=1,
            ))

        return chunks

    async def generate(
        self,
        requirements: Requirements,
        progress: Callable[[str], None] | None = None,
    ) -> list[TestCase]:
        chunks = self._build_chunks(requirements)
        all_cases: list[TestCase] = []
        for i, chunk in enumerate(chunks, 1):
            if progress:
                progress(f"Генерация: {chunk.label} ({i}/{len(chunks)})")
            for attempt in range(2):
                try:
                    cases = await self._generate_chunk(chunk)
                    all_cases.extend(cases)
                    break
                except json.JSONDecodeError:
                    if attempt == 0:
                        if progress:
                            progress(f"Повтор: {chunk.label}")
                    else:
                        if progress:
                            progress(f"Пропущен: {chunk.label}")
        for j, tc in enumerate(all_cases, 1):
            tc.id = f"TC-{j:03d}"
        return all_cases

    async def _generate_chunk(self, chunk: Chunk) -> list[TestCase]:
        prompt = (
            "Сгенерируй JSON-массив тест-кейсов.\n"
            f"По одному короткому кейсу на каждое требование ({chunk.item_count} шт).\n"
            "Каждый кейс — объект с полями: id, title, preconditions, "
            "steps (массив строк), expectedResult (строка).\n"
            "Пример: {\"id\":\"TC-001\",\"title\":\"Вход\","
            '"preconditions":"Юзер зарегистрирован",'
            '"steps":["Ввести логин","Нажать вход"],'
            '"expectedResult":"Юзер авторизован"}\n'
            "Не закрывай объект до конца всех полей. "
            "Только JSON-массив.\n\n"
            f"Заголовок: {chunk.prompt}\n"
        )
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 1500},
                },
            )
        response.raise_for_status()
        raw = response.json()["response"]
        data = _parse_json_response(raw)
        return [_to_testcase(item) for item in data]


_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


def _fix_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```")
        idx = text.rfind("```")
        if idx >= 0:
            text = text[:idx]
    text = _TRAILING_COMMA_RE.sub(r"\1", text)
    return text.strip()


def _parse_json_response(raw: str) -> list[dict]:
    text = _fix_json(raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_ARRAY_RE.search(text)
        if m:
            text = _fix_json(m.group(0))
            return json.loads(text)
        raise


def _to_str(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [str(v) for v in value if v is not None]
        return "; ".join(parts)
    return str(value) if value is not None else ""


def _to_str_list(value: object) -> list[str]:
    result: list[str] = []
    if isinstance(value, list):
        for v in value:
            if isinstance(v, list):
                s = _to_str(v[0]) if v else ""
                if s:
                    result.append(s)
            elif isinstance(v, str):
                result.append(v)
    return result


def _to_testcase(item: dict) -> TestCase:
    return TestCase(
        id=item["id"],
        title=item["title"],
        preconditions=_to_str(item.get("preconditions", "")),
        steps=_to_str_list(item.get("steps", [])),
        expected_result=_to_str(item["expectedResult"]),
    )


async def generate(
    requirements: Requirements,
    provider: LLMProvider,
    progress: Callable[[str], None] | None = None,
) -> list[TestCase]:
    return await provider.generate(requirements, progress=progress)
