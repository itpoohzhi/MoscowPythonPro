#!/usr/bin/env python3
import os
import subprocess
import sys
from io import TextIOWrapper

if hasattr(sys.stdout, "reconfigure") and isinstance(sys.stdout, TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure") and isinstance(sys.stderr, TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_step(step_num, title, cmd):
    print(f"\n[{step_num}/5] >>> {title}...")
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    if res.returncode != 0:
        print(f"❌ ПРОВЕРКА [{title}] ПРОВАЛЕНА (код {res.returncode}):")
        print(res.stdout)
        print(res.stderr)
        return False
    print(f"✅ [{title}] УСПЕШНО ПРОЙДЕНА")
    return True


def verify_techlead_gate():
    print("=" * 70)
    print("      КОНТРОЛЬНЫЙ ШЛЮЗ ТИМЛИДА (TECHLEAD GATE: 5 СТУПЕНЕЙ)")
    print("=" * 70)

    steps = [
        (1, "Синхронизация Базы Знаний", [sys.executable, "tools/verify_kb_sync.py"]),
        (
            2,
            "Построение AST-графа зависимостей",
            [sys.executable, "tools/build_dependency_graph.py"],
        ),
        (
            3,
            "Соблюдение границ архитектурных слоев",
            [sys.executable, "tools/verify_architecture_layers.py"],
        ),
        (
            4,
            "Бюджет зоны поражения (Blast Radius <= 7 файлов)",
            [sys.executable, "tools/verify_blast_radius.py"],
        ),
        (
            5,
            "Полный регрессионный тест-сьют (pytest)",
            ["uv", "run", "pytest", "tests/unit", "tests/integration", "-q"],
        ),
    ]

    for num, title, cmd in steps:
        if not run_step(num, title, cmd):
            print("\n" + "=" * 70)
            print("🚨 СТАТУС ПРИЁМКИ: ОТКЛОНЕНО ТИМЛИДОМ (TECHLEAD GATE: REJECTED)")
            print("=" * 70)
            return 1

    print("\n" + "=" * 70)
    print("🏆 СТАТУС ПРИЁМКИ: ОДОБРЕНО ТИМЛИДОМ (TECHLEAD GATE: ACCEPTED)")
    print("   Все 5 ступеней проверок пройдены со 100% результатом!")
    print("   Код допущен к объединению с основной веткой (Ready to Merge).")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(verify_techlead_gate())
