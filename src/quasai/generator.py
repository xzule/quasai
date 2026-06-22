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
            "ABSOLUTE LANGUAGE RULE (highest priority, applies to all text values in JSON):\n"
            "- Your entire output must be in English.\n"
            "- Use only standard Latin alphabet (a-z, A-Z) and common punctuation.\n"
            '- Words that look like transliterations from other languages (e.g., "юзер" → "user", '
            '"free-юзер" → "free-user") must be replaced with proper English.\n'
            "- Translate every word from the requirements into English.\n"
            "\n"
            "Generate test cases using ISTQB test design techniques:\n"
            "- Equivalence Partitioning: for each input or condition in the requirements, "
            "define valid and invalid equivalence classes and test at least one "
            "representative value from each class.\n"
            "- Boundary Value Analysis: scan the requirements for any numeric or temporal "
            "limits (e.g., maximum length, timeouts, credit caps, intervals, cooldown "
            "periods). For each such limit, generate tests for the exact boundary value, "
            "one just below, and one just above (if applicable). "
            "If the limit is inclusive, test both the boundary and the value immediately beyond it.\n"
            "- State Transition Testing: identify all explicit and implicit states "
            "(user roles, system modes, processing statuses, feature availability). "
            "Test both valid and invalid transitions, including unexpected events "
            "(errors, restarts, timeouts) \u2013 verify that every state is recoverable "
            "and the user can continue.\n"
            "\n"
            "Coverage: ensure every functional requirement (each bullet point or \u201cshall\u201d "
            "statement) is covered by at least one test case. "
            "If a requirement contains multiple distinct conditions (e.g., positive and negative cases), "
            "generate separate tests for each. "
            "Generate only distinct tests that verify different behaviors; "
            "skip cases that differ in only trivial details.\n"
            "\n"
            "Test case quality:\n"
            "- preconditions must be specific and measurable "
            '(e.g., "User has 0 credits" rather than "User has insufficient credits").\n'
            "- steps must be one atomic action per step.\n"
            "- expectedResult must be the actual verifiable outcome "
            "(e.g., exact error message text or a clear state change), "
            'rather than vague terms like "friendly message".\n'
            "\n"
            "Output exactly 5 fields per JSON object: "
            "id (string), title (string), preconditions (string), "
            "steps (array of strings), expectedResult (string). "
            "The JSON contains only these fields.\n"
            "\n"
            'Example:\n'
            '{"id":"TC-001",'
            '"title":"Register with password at minimum valid length",'
            '"preconditions":"Password policy requires 8-20 characters, '
            "alphanumeric; user is not registered.\","
            '"steps":["Enter username \'newuser\'",'
            "\"Enter password 'Pass1234' (exactly 8 characters)\",\"Click Register\"],"
            '"expectedResult":"Account created; user is logged in, '
            "state changes to 'active'; confirmation email sent.\"}\n"
            "\n"
            "Close the object only after all fields are written.\n"
            "\n"
            f"Requirements: {chunk.prompt}\n"
            "\n"
            "REMINDER: Output English only. "
            'Translate all non-English words (e.g., "юзер" → "user", "free-юзер" → "free-user"). '
            "Use only standard Latin alphabet (a-z, A-Z).\n"
            "<|end|>"
        )
        async with httpx.AsyncClient(timeout=None) as client:
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

        t1 = time.monotonic()
        print(f"--- Chunk '{chunk.label}' done in {t1-t0:.0f}s "
              f"({len(result)} cases) ---", flush=True)
        return result


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
