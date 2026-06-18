from dataclasses import dataclass, field


@dataclass
class Section:
    heading: str
    content: str
    subsections: list["Section"] = field(default_factory=list)


@dataclass
class Requirements:
    title: str
    sections: list[Section] = field(default_factory=list)


@dataclass
class TestCase:
    id: str
    title: str
    preconditions: str = ""
    steps: list[str] = field(default_factory=list)
    expected_result: str = ""
