import json
from pathlib import Path

from quasai.types import TestCase


_MAX_SIZE = 10 * 1024 * 1024


def _to_dict(tc: TestCase) -> dict:
    return {
        "id": tc.id,
        "title": tc.title,
        "preconditions": tc.preconditions,
        "steps": tc.steps,
        "expectedResult": tc.expected_result,
    }


def _from_dict(d: dict) -> TestCase:
    return TestCase(
        id=d["id"],
        title=d["title"],
        preconditions=d.get("preconditions", ""),
        steps=d.get("steps", []),
        expected_result=d.get("expectedResult", ""),
    )


def to_json(test_cases: list[TestCase], path: str) -> None:
    data = [_to_dict(tc) for tc in test_cases]
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    if len(raw.encode("utf-8")) > _MAX_SIZE:
        raise ValueError(
            "Размер результата превышает 10 МБ. "
            "Разбейте входные требования на несколько файлов "
            "и запустите генерацию для каждого отдельно"
        )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(raw)


def from_json(path: str) -> list[TestCase]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [_from_dict(d) for d in data]
