#!/usr/bin/env bash
set -euo pipefail

main() {
  local FORCE=0
  if [[ ${1:-} == "--force" || ${1:-} == "-f" ]]; then
    FORCE=1
    shift
  fi

  local SNAPSHOT=${1:-"snap-6"}

  if [[ $# -gt 1 ]]; then
    echo "Использование: restore_checkpoint.sh [--force|-f] <snap-0|...|snap-6>" >&2
    exit 2
  fi

  echo "=== ВОССТАНОВЛЕНИЕ КОНТРОЛЬНОГО СРЕЗА: $SNAPSHOT ==="

  case $SNAPSHOT in
    snap-0|snap-1|snap-2|snap-3|snap-4|snap-5|snap-6) ;;
    *)
      echo "Неизвестный срез: $SNAPSHOT. Доступные: snap-0 … snap-6"
      exit 1
      ;;
  esac

  local REPO_ROOT
  REPO_ROOT="$(git rev-parse --show-toplevel)"

  git fetch --tags origin 2>/dev/null || true
  if [[ $FORCE -eq 0 && -n "$(git status --porcelain)" ]]; then
    echo "❌ Ошибка: в рабочем дереве есть незакоммиченные изменения. Выполните 'git stash' или 'git commit' перед переключением на срез $SNAPSHOT." >&2
    exit 1
  fi

  if [[ $FORCE -eq 1 ]]; then
    git checkout -f "$SNAPSHOT"
  else
    git checkout "$SNAPSHOT"
  fi

  local WORKSHOP_DIR=""
  if [[ -f "$REPO_ROOT/workshop/pyproject.toml" ]]; then
    WORKSHOP_DIR="$REPO_ROOT/workshop"
  elif [[ -f "$REPO_ROOT/workshop-nov-5/pyproject.toml" ]]; then
    WORKSHOP_DIR="$REPO_ROOT/workshop-nov-5"
    if [[ ! -d "$WORKSHOP_DIR/.venv" && -d "$REPO_ROOT/workshop/.venv" ]]; then
      export UV_PROJECT_ENVIRONMENT="$REPO_ROOT/workshop/.venv"
    fi
  else
    echo "❌ Ошибка: не найден pyproject.toml в $REPO_ROOT/workshop или $REPO_ROOT/workshop-nov-5" >&2
    exit 1
  fi

  export UV_PYTHON="${UV_PYTHON:-3.14}"
  export UV_PYTHON_PREFERENCE="${UV_PYTHON_PREFERENCE:-only-managed}"

  cd "$WORKSHOP_DIR"

  case $SNAPSHOT in
    "snap-0")
      echo "Откат к исходному состоянию: единое приложение и 9 скилов Дней 1-2..."
      uv run pytest -q
      ;;
    "snap-1")
      echo "Развертывание Базы знаний (docs/INDEX.md)..."
      uv run python tools/verify_kb_sync.py
      ;;
    "snap-2")
      echo "Граф зависимостей монолита: проверка ацикличности..."
      uv run python tools/build_dependency_graph.py --check-cycles
      ;;
    "snap-3")
      echo "Требования EARS и конвейер GSD (Волна 1: Schemas)..."
      uv run pytest tests/unit/test_ears_requirements.py -q
      ;;
    "snap-4")
      echo "Линтер границ архитектурных слоёв..."
      uv run python tools/verify_architecture_layers.py
      ;;
    "snap-5")
      echo "Blast Radius Guard: бюджет изменений и замороженное ядро..."
      uv run python tools/verify_blast_radius.py
      ;;
    "snap-6")
      echo "Полный срез: 15 скилов, все верификаторы и Techlead Gate..."
      uv run python tools/verify_techlead_gate.py
      ;;
  esac

  echo "✅ Срез $SNAPSHOT успешно применен (каталог: $WORKSHOP_DIR)!"
  echo "💡 Для возврата на вершину ветки воркшопа выполните: git checkout main"
}

main "$@"
