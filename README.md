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

Place your `.md` file in the `input/` directory, then run:

```bash
./run.sh        # Linux / macOS
.\run.ps1       # Windows PowerShell
```

The script will prompt for the file name. Press `Ctrl+C` at any time to stop and clean up all containers. Results are saved to `./output/{filename}.json` and `./output/{filename}.csv`.

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

### JSON

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

### CSV

Columns: `id; title; preconditions; step1; step2; ...; stepN; expectedResult`.
Columns `step1` to `stepN` adapt to the maximum number of steps across all test cases.

```csv
id;title;preconditions;step1;step2;expectedResult
TC-001;Test case title;Preconditions;Step 1;Step 2;Expected result
```
