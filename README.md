# Quasai

Local test case generation from requirements via LLM.

## Installation

Requirements: Git, Docker (Linux) or Docker Desktop (Windows/macOS), 4+ GB RAM.

```bash
git clone https://github.com/xzule/quasai.git
cd quasai
```

## Usage

### Generate test cases

```bash
# Linux / macOS
./run.sh requirements.md

# Windows PowerShell
.\run.ps1 requirements.md
```

Place your `.md` file in the `input/` directory first. The script starts the LLM, runs generation, and stops all services automatically. Results are saved to `./output/{filename}.json` and `./output/{filename}.csv`.

## Input format

Markdown file with at least one heading (`#`, `##`, or `###`).

```markdown
# Project

## Requirement 1
Description.

### Sub-requirement 1.1
Details.
```

## Output format

```json
[
  {
    "id": "TC-001",
    "title": "Test case title",
    "preconditions": "Preconditions",
    "steps": ["Step 1", "Step 2"],
    "expectedResult": "Expected result"
  }
]
```
