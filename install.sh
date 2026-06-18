#!/usr/bin/env bash
set -euo pipefail

REPO="xzule/quasai"
GHCR="ghcr.io/$REPO"

echo "=== Quasai Installer ==="

if ! command -v docker &>/dev/null; then
    echo "Docker не найден. Устанавливаю..."
    curl -fsSL https://get.docker.com | sh
    if ! command -v docker &>/dev/null; then
        echo "Ошибка: не удалось установить Docker. Установите вручную: https://docs.docker.com/engine/install/"
        exit 1
    fi
    echo "Docker установлен."
fi

echo "Загружаю образ $GHCR:latest..."
docker pull "$GHCR:latest"

echo ""
echo "Установка завершена."
echo "Запуск: docker compose up"
echo "Генерация: quasai input.md -o output.json"