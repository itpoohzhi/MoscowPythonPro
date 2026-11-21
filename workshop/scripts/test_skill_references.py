from __future__ import annotations

import re
from pathlib import Path

WORKSHOP_ROOT = Path(__file__).resolve().parent.parent

# Ссылки на файлы внутри .agents/, .opencode/, .skills/ и skills/
REF_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"((?:\.agents|\.opencode|\.skills|skills)/[A-Za-z0-9_./-]+\.[a-z0-9]+)"
)


def _iter_docs() -> list[Path]:
    """Собрать все инструкции агентов, скилы и шаблоны промптов для проверки ссылок."""
    return sorted(
        [
            WORKSHOP_ROOT / "AGENTS.md",
            WORKSHOP_ROOT / ".agents" / "AGENTS.md",
            *(WORKSHOP_ROOT / ".agents" / "agents").glob("*.md"),
            *(WORKSHOP_ROOT / ".agents" / "prompts").glob("*.md"),
            *(WORKSHOP_ROOT / "skills").rglob("*.md"),
        ]
    )


def test_all_skill_and_agent_references_exist() -> None:
    """Все ссылки на .agents/agents/*, .agents/skills/* и skills/* должны указывать на существующие файлы."""
    missing: list[str] = []
    for doc in _iter_docs():
        text = doc.read_text(encoding="utf-8")
        rel_doc = doc.relative_to(WORKSHOP_ROOT)
        for match in REF_PATTERN.finditer(text):
            ref = match.group(1).rstrip(".,:;`)'\"")
            if any(ch in ref for ch in "<>*{}") or "..." in ref:
                continue
            if not (WORKSHOP_ROOT / ref).exists():
                missing.append(f"{rel_doc} -> {ref}")
    assert not missing, "Найдены битые ссылки:\n" + "\n".join(sorted(set(missing)))


def test_agents_md_contains_language_table() -> None:
    """В .agents/AGENTS.md должна присутствовать таблица «Язык общения», на которую ссылаются скилы."""
    agents_md = (WORKSHOP_ROOT / ".agents" / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Язык общения" in agents_md
    assert "| Где | Какой язык |" in agents_md


def test_skill_mirrors_are_identical() -> None:
    """Все три зеркала скилов (skills/, .agents/skills/, .opencode/skills/) должны быть байт-в-байт одинаковы."""
    base_dir = WORKSHOP_ROOT / "skills"
    base_files = {
        p.relative_to(base_dir): p.read_bytes() for p in base_dir.rglob("*") if p.is_file()
    }
    for mirror in (WORKSHOP_ROOT / ".agents" / "skills", WORKSHOP_ROOT / ".opencode" / "skills"):
        mirror_files = {
            p.relative_to(mirror): p.read_bytes() for p in mirror.rglob("*") if p.is_file()
        }
        assert mirror_files == base_files, f"Рассинхрон зеркала {mirror.relative_to(WORKSHOP_ROOT)}"
