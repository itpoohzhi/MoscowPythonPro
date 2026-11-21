#!/usr/bin/env python3
"""Утилита переключения режима работы: с процедурными скилами или без них (vibe-coding demo).

Скрывает и возвращает все три каталога скилов (`.agents/skills`, `.opencode/skills`, `skills`),
чтобы OpenCode в режиме `--disable` гарантированно не подхватывал ни один скил, а `git status`
оставался чистым (`--assume-unchanged`).
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_TARGETS: tuple[tuple[str, str], ...] = (
    (".agents/skills", "agents_skills"),
    (".opencode/skills", "opencode_skills"),
    ("skills", "skills"),
)
REPO_HASH = hashlib.sha256(str(REPO_ROOT).encode("utf-8")).hexdigest()[:8]
STASH_DIR = Path.home() / ".cache" / "moscowpython-skills-stash" / REPO_HASH


def get_tracked_files(rel_dir: str) -> list[str]:
    res = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", rel_dir],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]


def disable_skills() -> int:
    existing = [
        (rel, key, REPO_ROOT / rel) for rel, key in SKILL_TARGETS if (REPO_ROOT / rel).exists()
    ]
    if not existing:
        print("⚠️  Каталоги скилов не найдены или уже отключены.")
        return 0

    STASH_DIR.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for rel, key, src in existing:
        tracked = get_tracked_files(rel)
        if tracked:
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "update-index", "--assume-unchanged", *tracked],
                check=True,
            )
        dst = STASH_DIR / key
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))
        moved.append(rel)

    print(f"🔒 [SKILLS DISABLED] Скилы перемещены в {STASH_DIR}: {', '.join(moved)}.")
    print("   Git не считает файлы удалёнными (--assume-unchanged).")
    print("   Агент теперь работает в «диком» режиме вайб-кодинга (0 скилов в проекте).")
    return 0


def enable_skills() -> int:
    if not STASH_DIR.exists() or not any((STASH_DIR / key).exists() for _, key in SKILL_TARGETS):
        agents_dir = REPO_ROOT / ".agents" / "skills"
        if agents_dir.exists():
            count = sum(1 for p in agents_dir.iterdir() if p.is_dir())
            print(f"✅ Скилы уже активны ({count} процедур в .agents/skills).")
            return 0
        print("⚠️  Резервная копия скилов не найдена в stash.")
        return 1

    restored: list[str] = []
    for rel, key in SKILL_TARGETS:
        src = STASH_DIR / key
        dst = REPO_ROOT / rel
        if not src.exists():
            continue
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        tracked = get_tracked_files(rel)
        if tracked:
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "update-index", "--no-assume-unchanged", *tracked],
                check=True,
            )
        restored.append(rel)

    try:
        STASH_DIR.rmdir()
    except OSError:
        pass

    agents_dir = REPO_ROOT / ".agents" / "skills"
    count = sum(1 for p in agents_dir.iterdir() if p.is_dir()) if agents_dir.exists() else 0
    print(
        f"🔓 [SKILLS ENABLED] Скилы возвращены ({', '.join(restored)}; {count} процедур доступно)."
    )
    print("   Агент снова вооружен процедурными контрактами и L1-L3 инструкциями.")
    return 0


def status_skills() -> int:
    active = [rel for rel, _ in SKILL_TARGETS if (REPO_ROOT / rel).exists()]
    if active:
        agents_dir = REPO_ROOT / ".agents" / "skills"
        count = sum(1 for p in agents_dir.iterdir() if p.is_dir()) if agents_dir.exists() else 0
        print(f"🟢 Скилы АКТИВНЫ ({', '.join(active)}; {count} процедур)")
    else:
        print(f"🔴 Скилы ОТКЛЮЧЕНЫ (находятся в {STASH_DIR})")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if cmd in ("--disable", "disable", "off"):
        sys.exit(disable_skills())
    elif cmd in ("--enable", "enable", "on"):
        sys.exit(enable_skills())
    elif cmd in ("--status", "status"):
        sys.exit(status_skills())
    else:
        print("Использование: python3 tools/toggle_skills.py [--disable | --enable | --status]")
        sys.exit(1)
