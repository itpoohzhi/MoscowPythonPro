#!/usr/bin/env bash
set -euo pipefail

echo "======================================================="
echo "Инициализация и валидация проекта linksvc"
echo "======================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSHOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if REPO_ROOT="$(git -C "$WORKSHOP_DIR" rev-parse --show-toplevel 2>/dev/null)" && [[ -d "$REPO_ROOT/workshop" ]]; then
  WORKSHOP_DIR="$REPO_ROOT/workshop"
fi
cd "$WORKSHOP_DIR"

echo "1. Синхронизация зависимостей через uv..."
uv sync --python 3.14 --python-preference only-managed

echo "2. Проверка линтерами (ruff + basedpyright)..."
uv run ruff check app tests
uv run basedpyright

echo "3. Прогон набора тестов..."
uv run pytest -q

echo "======================================================="
echo "Проект linksvc успешно инициализирован и верифицирован!"
echo "======================================================="
