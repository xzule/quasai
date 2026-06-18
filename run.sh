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

INPUT_LEAF="$(basename "$INPUT_FILE")"
INPUT_DEST="$PROJECT_DIR/input/$INPUT_LEAF"
if [ "$(realpath "$INPUT_FILE" 2>/dev/null)" != "$(realpath "$INPUT_DEST" 2>/dev/null)" ]; then
    cp "$INPUT_FILE" "$INPUT_DEST"
fi

docker compose -p quasai up -d ollama

docker compose -p quasai run --rm --entrypoint quasai app \
    "/input/$INPUT_LEAF" \
    "-o/output/$(basename "$OUTPUT_FILE")"

OUTPUT_LEAF="$(basename "$OUTPUT_FILE")"
OUTPUT_TEMP="$PROJECT_DIR/output/$OUTPUT_LEAF"
if [ "$(realpath "$OUTPUT_FILE" 2>/dev/null)" != "$(realpath "$OUTPUT_TEMP" 2>/dev/null)" ]; then
    cp "$OUTPUT_TEMP" "$OUTPUT_FILE"
fi

docker compose -p quasai down

echo "Done: $OUTPUT_FILE"
