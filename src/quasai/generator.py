import json

import httpx

from quasai.types import Requirements, TestCase

_DEFAULT_MODEL = "phi4-mini"
_DEFAULT_URL = "http://ollama:11434"


class LLMProvider:
    async def generate(self, requirements: Requirements) -> list[TestCase]:
        ...


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        base_url: str = _DEFAULT_URL,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")

    async def generate(self, requirements: Requirements) -> list[TestCase]:
        prompt = (
            "Ты — генератор тестовых сценариев. "
            "На основе требований ниже составь список тест-кейсов "
            "в формате JSON. Каждый объект должен содержать поля: "
            "id, title, preconditions, steps (массив строк), "
            "expectedResult, tags (массив строк). "
            "Верни ТОЛЬКО JSON-массив, без пояснений.\n\n"
            f"Заголовок: {requirements.title}\n"
        )
        for section in requirements.sections:
            prompt += f"\nРаздел: {section.heading}\n{section.content}\n"
            for sub in section.subsections:
                prompt += f"\nПодраздел: {sub.heading}\n{sub.content}\n"

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
        response.raise_for_status()
        raw = response.json()["response"]
        data = json.loads(raw)
        return [
            TestCase(
                id=item["id"],
                title=item["title"],
                preconditions=item.get("preconditions", ""),
                steps=item.get("steps", []),
                expected_result=item["expectedResult"],
                tags=item.get("tags", []),
            )
            for item in data
        ]


async def generate(
    requirements: Requirements,
    provider: LLMProvider,
) -> list[TestCase]:
    return await provider.generate(requirements)
