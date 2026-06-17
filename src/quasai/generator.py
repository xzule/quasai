from collections.abc import Awaitable

from quasai.types import Requirements, TestCase


class LLMProvider:
    async def generate(self, requirements: Requirements) -> list[TestCase]:
        ...
