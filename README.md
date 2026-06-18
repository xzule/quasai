# Quasai

Local test case generation from requirements via LLM.

## Installation

Requirements: Docker (Linux) or Docker Desktop (Windows/macOS), 4+ GB RAM.

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/xzule/quasai/main/install.sh | sh
```

### Windows

1. Install Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/
2. Run PowerShell as Administrator:

```powershell
irm https://raw.githubusercontent.com/xzule/quasai/main/install.ps1 | iex
```

## Usage

### 1. Clone the repository

```bash
git clone https://github.com/xzule/quasai.git
cd quasai
```

### 2. Prepare input

Create an `input` directory and place your `.md` requirements file there:

```bash
mkdir -p input
# copy or create input/requirements.md
```

### 3. Start services and generate

**Linux / macOS / Windows:**

```bash
docker compose up -d
docker compose exec app quasai /input/requirements.md -o /output/tests.json
```

The result will appear in `./output/tests.json`.

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
    "expectedResult": "Expected result",
    "tags": ["positive", "smoke"]
  }
]
```
