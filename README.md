# MoscowPythonPro — AI Engineering Workshop

[![MoscowPython](./assets/moscowpython-logo.png)](./assets/moscowpython-logo.svg)

Материалы воркшопа **MoscowPythonPro**, который пройдёт 5 ноября 2026 года. Репозиторий показывает, как перейти от вайб-кодинга к управляемой AI-разработке на примере FastAPI-микросервиса `linksvc`.

## Структура репозитория

- [`workshop-nov-5/`](./workshop-nov-5/) — исходники учебного микросервиса, скилы, тесты и верификаторы.
- [`workshop-nov-5/.agents/skills/`](./workshop-nov-5/.agents/skills/) — 28 каталогов процедурных скилов: 15 скилов базовой лестницы воркшопа и 13 инженерных скилов AI-SDLC; рядом лежит symlink `teamlead-gate` на `techlead-gate`.
- [`assets/`](./assets/) — графические материалы MoscowPythonPro в PNG и SVG.

Учебные материалы воркшопа (`ПРЕРЕКВИЗИТЫ.md`, `Ранбук-MoscowPythonPro-5-ноября.md`,
`Приложение-А-Справочник-кода-и-окружения.md`, `СБОРКА.md`) входят в локальный комплект
материалов участника MoscowPythonPro (размещаются в рабочей папке рядом с клоном
репозитория) и по решению организаторов не публикуются в Git-историю микросервиса.

Контрольный срез можно открыть командой `git checkout snap-3` или безопасным помощником
`cd workshop-nov-5 && ./tools/restore_checkpoint.sh snap-3`.

## Быстрый старт

Нужны Python 3.14 и [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/itpoohzhi/MoscowPythonPro.git ~/work/MoscowPythonPro
cd ~/work/MoscowPythonPro
git switch workshop-nov-5
cd workshop-nov-5

uv sync
uv run ruff check .
uv run pytest -q
uv run python tools/verify_techlead_gate.py
```

Подробное описание микросервиса, учебных срезов и инструментов находится в [`workshop-nov-5/README.md`](./workshop-nov-5/README.md).
