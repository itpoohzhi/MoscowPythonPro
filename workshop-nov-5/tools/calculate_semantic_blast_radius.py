#!/usr/bin/env python3
import sys
from pathlib import Path as _Path

sys.path.insert(
    0, str(_Path(__file__).resolve().parents[1])
)  # корень проекта: импорт `app` и `tools`

import subprocess
import sys
from pathlib import Path

from tools.build_dependency_graph import build_graph


def get_modified_modules() -> list[str]:
    """Вернуть изменённые файлы приложения относительно каталога воркшопа."""
    status = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
    )
    prefix_result = subprocess.run(
        ["git", "rev-parse", "--show-prefix"], capture_output=True, text=True, check=True
    )
    prefix = prefix_result.stdout.strip()
    modules: list[str] = []
    for line in status.stdout.splitlines():
        if not line.strip():
            continue
        filepath = line.strip().split()[-1]
        if prefix and filepath.startswith(prefix):
            filepath = filepath[len(prefix) :]
        elif filepath.startswith("workshop-nov-5/"):
            filepath = filepath.removeprefix("workshop-nov-5/")
        if filepath.startswith("app/"):
            modules.append(filepath)
    return modules


def calculate_blast():
    root = Path.cwd()
    changed_files = get_modified_modules()

    if not changed_files:
        print("✅ Изменений в рабочей директории нет (Семантический Blast Radius = 0).")
        return 0

    graph = build_graph(root)
    # Инвертируем граф для поиска downstream зависимостей
    dependents = {}
    for src, targets in graph.items():
        for t in targets:
            dependents.setdefault(t, set()).add(src)

    print("=== РАСЧЕТ СЕМАНТИЧЕСКОГО РАДИУСА ПОРАЖЕНИЯ (BLAST RADIUS) ===")
    total_impacted = set()
    for f in changed_files:
        mod = f.replace("/", ".").replace(".py", "")
        downstream = dependents.get(mod, set())
        total_impacted.update(downstream)
        print(f"Файл: {f} -> Прямых зависимых модулей: {len(downstream)}")
        for d in sorted(downstream):
            print(f"   [!] Затронут: {d}")

    print(f"\nИТОГО СЕМАНТИЧЕСКИЙ РАДИУС: {len(total_impacted)} модулей под риском регрессии")
    if len(total_impacted) > 10:
        print(
            "⚠️ ВНИМАНИЕ: Высокий семантический радиус! Требуется запуск полного регрессионного сьюта."
        )
    return 0


if __name__ == "__main__":
    calculate_blast()
