import re

from quasai.types import Requirements, Section


def parse_markdown(path: str) -> Requirements:
    with open(path) as f:
        lines = f.readlines()

    content = "".join(lines).strip()
    if not content:
        raise ValueError("Файл не содержит требований")

    title = ""
    sections: list[Section] = []
    current_section: Section | None = None
    current_subsection: Section | None = None
    current_text: list[str] = []

    heading_re = re.compile(r"^(#{1,3})\s+(.+)$")

    for line in lines:
        m = heading_re.match(line)
        if m:
            _flush_text(current_section, current_subsection, current_text)
            current_text = []
            level = len(m.group(1))
            text = m.group(2).strip()

            if level == 1:
                title = text
            elif level == 2:
                current_section = Section(heading=text, content="")
                sections.append(current_section)
                current_subsection = None
            elif level == 3:
                if current_section is None:
                    current_section = Section(heading="", content="")
                    sections.append(current_section)
                current_subsection = Section(heading=text, content="")
                current_section.subsections.append(current_subsection)
        else:
            current_text.append(line)

    _flush_text(current_section, current_subsection, current_text)

    if not title and not sections:
        raise ValueError("Файл не содержит требований")

    return Requirements(title=title, sections=sections)


_ITEM_RE = re.compile(r"^\s*\d+(\.\d+)+\s", re.MULTILINE)


def count_items(content: str) -> int:
    return len(_ITEM_RE.findall(content))


def _flush_text(
    section: Section | None,
    subsection: Section | None,
    text: list[str],
) -> None:
    stripped = "".join(text).strip()
    if not stripped:
        return
    if subsection is not None:
        subsection.content = (subsection.content + "\n" + stripped).strip()
    elif section is not None:
        section.content = (section.content + "\n" + stripped).strip()
