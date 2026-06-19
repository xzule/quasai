import asyncio
import json
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from quasai.parser import count_items
from quasai.types import Requirements, Section, TestCase

_DEFAULT_MODEL = "phi4-mini"
_DEFAULT_URL = "http://ollama:11434"
_CHUNK_SIZE = 3

_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


@dataclass
class Chunk:
    prompt: str
    label: str


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
        buffer_label = requirements.title or "Requirements"

        def flush(label: str) -> None:
            nonlocal buffer_parts, buffer_count
            if not buffer_parts:
                return
            prompt = "\n".join(buffer_parts)
            chunks.append(Chunk(prompt=prompt, label=label))
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
                label=requirements.title or "Requirements",
            ))

        return chunks

    async def generate(
        self,
        requirements: Requirements,
        progress: Callable[[str], None] | None = None,
    ) -> list[TestCase]:
        t0 = time.monotonic()
        chunks = self._build_chunks(requirements)
        all_cases: list[TestCase] = []
        for i, chunk in enumerate(chunks, 1):
            if progress:
                progress(f"Generating: {chunk.label} ({i}/{len(chunks)})")
            for attempt in range(2):
                try:
                    cases = await self._generate_chunk(chunk)
                    all_cases.extend(cases)
                    break
                except (json.JSONDecodeError, httpx.HTTPError) as exc:
                    if attempt == 0:
                        if progress:
                            progress(f"Retry: {chunk.label} ({type(exc).__name__})")
                        await asyncio.sleep(10)
                    else:
                        if progress:
                            progress(f"Skipped: {chunk.label} ({type(exc).__name__})")
        for j, tc in enumerate(all_cases, 1):
            tc.id = f"TC-{j:03d}"
        t1 = time.monotonic()
        print(f"--- TOTAL: {t1-t0:.0f}s, {len(all_cases)} cases ---", flush=True)
        return all_cases

    async def _generate_chunk(self, chunk: Chunk) -> list[TestCase]:
        t0 = time.monotonic()
        prompt = (
            "<|user|>\n"
            "Write ONLY in English. Use only Latin letters a-z A-Z. "
            "Do NOT use Russian, Cyrillic, or any non-Latin characters.\n"
            "\n"
            "Generate test cases using ISTQB test design techniques:\n"
            "- Equivalence Partitioning: cover valid (positive) and invalid (negative) equivalence classes\n"
            "- Boundary Value Analysis: when numeric ranges or limits exist, "
            "test boundary values (min, just below min, max, just above max)\n"
            "- State Transition Testing: when requirements describe states, "
            "statuses, or workflows, test valid and invalid state transitions\n"
            "\n"
            "Output ONLY a JSON array of flat objects. "
            "Each object MUST have exactly these 5 fields: "
            "id (string), title (string), preconditions (string), "
            "steps (array of strings), expectedResult (string). "
            "Do NOT add technique names, equivalence classes, boundary values, "
            "state transitions, or any other fields.\n"
            "\n"
            'Example:\n'
            '{"id":"TC-001",'
            '"title":"Login with password at minimum length",'
            '"preconditions":"User is registered, minimum password length is 8 characters",'
            '"steps":["Enter username","Enter 8-character password","Click Login"],'
            '"expectedResult":"User is logged in"}\n'
            "\n"
            "Do not close the object before all fields are written.\n"
            "\n"
            f"Requirements: {chunk.prompt}\n"
            "\n"
            "Write ONLY in English. Use only Latin letters a-z A-Z. "
            "Do NOT use Russian, Cyrillic, or any non-Latin characters.\n"
            "<|end|>"
        )
        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": 0.0},
                },
            ) as resp:
                lines = [l async for l in resp.aiter_lines() if l]
            raw = "".join(json.loads(ch)["response"] for ch in lines)
        data = _parse_json_response(raw)
        result = [_to_testcase(item) for item in data]
        result = [tc for tc in result if tc is not None]

        dirty = [tc for tc in result if _has_cyrillic(tc)]
        if dirty:
            clean = [tc for tc in result if not _has_cyrillic(tc)]
            sanitized = await self._sanitize_objects(dirty)
            result = clean + sanitized

        t1 = time.monotonic()
        print(f"--- Chunk '{chunk.label}' done in {t1-t0:.0f}s "
              f"({len(result)} cases, {len(dirty)} sanitized) ---", flush=True)
        return result

    async def _sanitize_objects(self, cases: list[TestCase]) -> list[TestCase]:
        obj_list = [
            {"id": c.id, "title": c.title, "preconditions": c.preconditions,
             "steps": c.steps, "expectedResult": c.expected_result}
            for c in cases
        ]
        prompt = (
            "<|user|>\n"
            "Replace any non-Latin characters with Latin equivalents "
            "in the following JSON array. Keep the JSON structure identical.\n"
            "\n"
            f"{json.dumps(obj_list, ensure_ascii=False)}\n"
            "\n"
            "Output ONLY the JSON array.\n"
            "<|end|>"
        )
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": 0.0},
                },
            ) as resp:
                lines = [l async for l in resp.aiter_lines() if l]
        raw = "".join(json.loads(ch)["response"] for ch in lines)
        try:
            data = _parse_json_response(raw)
            translated = [to for item in data if (to := _to_testcase(item)) is not None]
            if translated:
                return translated
        except json.JSONDecodeError:
            pass
        return cases  # fallback — keep original


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


def _extract_array(text: str) -> str:
    """Extract from first '[' to end, ignoring preamble."""
    idx = text.find("[")
    if idx >= 0:
        return text[idx:]
    return text


def _extract_complete_objects(text: str) -> list[str]:
    """Extract substrings of complete JSON objects { ... }."""
    objs: list[str] = []
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                objs.append(text[start:i+1])
                start = -1
    return objs


def _parse_json_response(raw: str) -> list[dict]:
    text = _fix_json(raw)
    # Try full-parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting the array block with [ ... ]
    m = _JSON_ARRAY_RE.search(text)
    if m:
        try:
            return json.loads(_fix_json(m.group(0)))
        except json.JSONDecodeError:
            pass
    # Fallback: extract individual complete objects
    text = _extract_array(text)
    items: list[dict] = []
    for obj_str in _extract_complete_objects(text):
        try:
            item = json.loads(obj_str)
            if "id" in item and "title" in item and "expectedResult" in item:
                items.append(item)
        except json.JSONDecodeError:
            pass
    if items:
        return items
    print(f"--- FAILED JSON ---\n{text[:1500]}\n--- END ---", file=sys.stderr, flush=True)
    raise json.JSONDecodeError("No valid objects found", text, 0)


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


def _has_cyrillic(tc: TestCase) -> bool:
    for val in (tc.id, tc.title, tc.preconditions, tc.expected_result):
        if any(ord(c) > 127 for c in val):
            return True
    for step in tc.steps:
        if any(ord(c) > 127 for c in step):
            return True
    return False


def _to_testcase(item: dict) -> TestCase | None:
    if not all(k in item for k in ("id", "title", "expectedResult")):
        return None
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
