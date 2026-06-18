import json

import httpx
import pytest

from quasai.generator import LLMProvider, OllamaProvider, generate
from quasai.types import Requirements, Section, TestCase


class MockProvider(LLMProvider):
    def __init__(self, result: list[TestCase] | None = None) -> None:
        self._result = result or []

    async def generate(self, requirements: Requirements) -> list[TestCase]:
        return self._result


@pytest.mark.asyncio
async def test_generate_with_mock() -> None:
    expected = [
        TestCase(id="TC-001", title="Test"),
        TestCase(id="TC-002", title="Test 2"),
    ]
    provider = MockProvider(expected)
    req = Requirements(title="Test", sections=[])

    result = await generate(req, provider)

    assert result == expected


@pytest.mark.asyncio
async def test_generate_empty_result() -> None:
    provider = MockProvider([])
    req = Requirements(title="Empty")

    result = await generate(req, provider)

    assert result == []


@pytest.mark.asyncio
async def test_ollama_provider_connection_error() -> None:
    provider = OllamaProvider(model="test-model", base_url="http://localhost:1")
    req = Requirements(title="Test")

    with pytest.raises(httpx.ConnectError):
        await provider.generate(req)


@pytest.mark.asyncio
async def test_ollama_provider_bad_json(httpx_mock) -> None:
    httpx_mock.add_response(
        url="http://ollama:11434/api/generate",
        json={"response": "not json at all"},
    )
    provider = OllamaProvider(model="phi4-mini")
    req = Requirements(title="Test")

    with pytest.raises(json.JSONDecodeError):
        await provider.generate(req)
