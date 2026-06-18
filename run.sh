#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 2 ]; then
    echo "Usage: $0 <input.md> <output.json>"
    echo ""
    echo "Example:"
    echo "  $0 input/requirements.md output/tests.json"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: input file not found: $INPUT_FILE"
    exit 1
fi

mkdir -p "$PROJECT_DIR/input"
mkdir -p "$PROJECT_DIR/output"

cp "$INPUT_FILE" "$PROJECT_DIR/input/"

docker compose -p quasai up -d ollama

docker compose -p quasai run --rm --entrypoint quasai app \
    "/input/$(basename "$INPUT_FILE")" \
    "-o/output/$(basename "$OUTPUT_FILE")"

cp "$PROJECT_DIR/output/$(basename "$OUTPUT_FILE")" "$OUTPUT_FILE"

docker compose -p quasai down

echo "Done: $OUTPUT_FILE"
