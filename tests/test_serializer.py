import json
from pathlib import Path

import pytest

from quasai.serializer import to_json, from_json
from quasai.types import TestCase


def test_to_json_basic(tmp_path: Path) -> None:
    cases = [
        TestCase(
            id="TC-001",
            title="Login with valid credentials",
            preconditions="User is on login page",
            steps=["Enter username", "Enter password", "Click Login"],
            expected_result="User is redirected to dashboard",
            tags=["positive", "smoke"],
        ),
        TestCase(
            id="TC-002",
            title="Login with invalid password",
            preconditions="User is on login page",
            steps=["Enter username", "Enter wrong password", "Click Login"],
            expected_result="Error message is displayed",
            tags=["negative"],
        ),
    ]
    path = tmp_path / "out.json"

    to_json(cases, str(path))

    with open(path) as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["id"] == "TC-001"
    assert data[0]["title"] == "Login with valid credentials"
    assert data[0]["steps"] == ["Enter username", "Enter password", "Click Login"]
    assert data[0]["tags"] == ["positive", "smoke"]


def test_to_json_empty(tmp_path: Path) -> None:
    path = tmp_path / "empty.json"

    to_json([], str(path))

    with open(path) as f:
        data = json.load(f)

    assert data == []


def test_round_trip(tmp_path: Path) -> None:
    original = [
        TestCase(
            id="TC-001",
            title="Test A",
            preconditions="None",
            steps=["Step 1"],
            expected_result="OK",
            tags=["a"],
        ),
        TestCase(
            id="TC-002",
            title="Test B",
            preconditions="Logged in",
            steps=["Step 1", "Step 2"],
            expected_result="Done",
            tags=[],
        ),
    ]
    path = tmp_path / "roundtrip.json"

    to_json(original, str(path))
    restored = from_json(str(path))

    assert len(restored) == len(original)
    for r, o in zip(restored, original):
        assert r.id == o.id
        assert r.title == o.title
        assert r.preconditions == o.preconditions
        assert r.steps == o.steps
        assert r.expected_result == o.expected_result
        assert r.tags == o.tags


def test_to_json_exceeds_10mb(tmp_path: Path) -> None:
    cases = [
        TestCase(
            id=f"TC-{i:04d}",
            title="Long " * 2000,
            preconditions="Pre " * 2000,
            steps=["Step " * 2000],
            expected_result="Res " * 2000,
            tags=["tag"] * 50,
        )
        for i in range(500)
    ]
    path = tmp_path / "large.json"

    with pytest.raises(ValueError, match="10 МБ"):
        to_json(cases, str(path))


def test_to_json_creates_parent_dirs(tmp_path: Path) -> None:
    cases = [TestCase(id="TC-001", title="Test")]
    path = tmp_path / "subdir" / "out.json"

    to_json(cases, str(path))

    assert path.exists()
    with open(path) as f:
        data = json.load(f)
    assert data[0]["id"] == "TC-001"
