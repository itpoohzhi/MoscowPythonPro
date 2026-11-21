# MoscowPythonPro — AI Engineering Workshop

[![MoscowPython](./assets/moscowpython-logo.png)](./assets/moscowpython-logo.svg)

Материалы воркшопа **MoscowPythonPro** (2026). Репозиторий показывает, как перейти от вайб-кодинга к управляемой AI-разработке на примере FastAPI-микросервиса `linksvc`.

## Структура репозитория

- [`ПРЕРЕКВИЗИТЫ.md`](./ПРЕРЕКВИЗИТЫ.md) — подготовка окружения (Python 3.14 через `uv`, PostgreSQL 17, OpenCode CLI).
- [`Ранбук-MoscowPythonPro.md`](./Ранбук-MoscowPythonPro.md) — основной ранбук воркшопа (Части I–IV и все живые промпты).
- [`Приложение-А-Справочник-кода-и-окружения.md`](./Приложение-А-Справочник-кода-и-окружения.md) — справочник кода и конфигураций.
- [`workshop/`](./workshop/) — исходники учебного микросервиса `linksvc`, 29 процедурных скилов (`.agents/skills/`), 10 инженерных справочников (`.agents/agents/`), тесты и верификаторы.
- [`assets/`](./assets/) — графические материалы MoscowPythonPro в PNG и SVG.

Контрольный срез можно открыть командой `git checkout snap-3` или безопасным помощником
`cd workshop && ./tools/restore_checkpoint.sh snap-3`.

## Быстрый старт

Нужны Python 3.14 и [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/itpoohzhi/MoscowPythonPro.git ~/work/MoscowPythonPro
cd ~/work/MoscowPythonPro
git switch main
cd workshop

uv sync
uv run ruff check .
uv run pytest -q
uv run python tools/verify_techlead_gate.py
```

Подробное описание микросервиса, учебных срезов и инструментов находится в [`workshop/README.md`](./workshop/README.md).
