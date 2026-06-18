#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <filename.md>"
    echo ""
    echo "Place your .md file in the input/ directory and pass just the filename:"
    echo "  $0 requirements.md"
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT_FILE="$PROJECT_DIR/input/$1"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: file not found in $PROJECT_DIR/input"
    echo "Place your .md file in the input/ directory."
    exit 1
fi

docker compose -p quasai up -d ollama

docker compose -p quasai run --rm --entrypoint quasai app "/input/$1"

docker compose -p quasai down
