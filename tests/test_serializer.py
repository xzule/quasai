import csv
import json
from pathlib import Path

import pytest

from quasai.serializer import from_json, to_csv, to_json
from quasai.types import TestCase


def test_to_json_basic(tmp_path: Path) -> None:
    cases = [
        TestCase(
            id="TC-001",
            title="Login with valid credentials",
            preconditions="User is on login page",
            steps=["Enter username", "Enter password", "Click Login"],
            expected_result="User is redirected to dashboard",
        ),
        TestCase(
            id="TC-002",
            title="Login with invalid password",
            preconditions="User is on login page",
            steps=["Enter username", "Enter wrong password", "Click Login"],
            expected_result="Error message is displayed",
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
        ),
        TestCase(
            id="TC-002",
            title="Test B",
            preconditions="Logged in",
            steps=["Step 1", "Step 2"],
            expected_result="Done",
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


def test_to_json_exceeds_10mb(tmp_path: Path) -> None:
    cases = [
        TestCase(
            id=f"TC-{i:04d}",
            title="Long " * 2000,
            preconditions="Pre " * 2000,
            steps=["Step " * 2000],
            expected_result="Res " * 2000,
        )
        for i in range(500)
    ]
    path = tmp_path / "large.json"

    with pytest.raises(ValueError, match="10 MB"):
        to_json(cases, str(path))


def test_to_json_creates_parent_dirs(tmp_path: Path) -> None:
    cases = [TestCase(id="TC-001", title="Test")]
    path = tmp_path / "subdir" / "out.json"

    to_json(cases, str(path))

    assert path.exists()
    with open(path) as f:
        data = json.load(f)
    assert data[0]["id"] == "TC-001"


def test_to_csv_equal_steps(tmp_path: Path) -> None:
    cases = [
        TestCase(id="TC-001", title="A", preconditions="P1", steps=["Step 1", "Step 2"], expected_result="R1"),
        TestCase(id="TC-002", title="B", preconditions="P2", steps=["Step 3", "Step 4"], expected_result="R2"),
    ]
    path = tmp_path / "out.csv"

    to_csv(cases, str(path))

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)
    assert rows[0] == ["id", "title", "preconditions", "step0", "step1", "expectedResult"]
    assert rows[1] == ["TC-001", "A", "P1", "Step 1", "Step 2", "R1"]
    assert rows[2] == ["TC-002", "B", "P2", "Step 3", "Step 4", "R2"]


def test_to_csv_unequal_steps(tmp_path: Path) -> None:
    cases = [
        TestCase(id="TC-001", title="A", steps=["Step 1", "Step 2", "Step 3"], expected_result="R1"),
        TestCase(id="TC-002", title="B", steps=["Step 1"], expected_result="R2"),
    ]
    path = tmp_path / "out.csv"

    to_csv(cases, str(path))

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)
    assert rows[0] == ["id", "title", "preconditions", "step0", "step1", "step2", "expectedResult"]
    assert rows[1] == ["TC-001", "A", "", "Step 1", "Step 2", "Step 3", "R1"]
    assert rows[2] == ["TC-002", "B", "", "Step 1", "", "", "R2"]


def test_to_csv_empty(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"

    to_csv([], str(path))

    with open(path, encoding="utf-8-sig") as f:
        content = f.read()
    assert content.strip() == "id;title;preconditions;expectedResult"


def test_to_csv_bom(tmp_path: Path) -> None:
    cases = [TestCase(id="TC-001", title="Test")]
    path = tmp_path / "bom.csv"

    to_csv(cases, str(path))

    with open(path, "rb") as f:
        raw = f.read(3)
    assert raw == b"\xef\xbb\xbf"
