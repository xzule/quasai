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
./run.sh input/requirements.md output/tests.json

# Windows PowerShell
.\run.ps1 -InputFile input/requirements.md -OutputFile output/tests.json
```

The script starts the LLM, runs generation, waits for the result, and stops all services automatically. The result is saved to the specified output path.

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
