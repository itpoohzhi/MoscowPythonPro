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

### Вариант 1 — локально (Python 3.14 + [uv](https://docs.astral.sh/uv/))

```bash
git clone -b main https://github.com/itpoohzhi/MoscowPythonPro.git ~/work/MoscowPythonPro
cd ~/work/MoscowPythonPro/workshop
test -f .env || cp .env.example .env && chmod 600 .env
docker compose up -d db
uv sync --python 3.14 --python-preference only-managed
uv run alembic upgrade head
uv run ruff check .
uv run pytest -ra
uv run python tools/verify_techlead_gate.py
```

### Вариант 2 — всё готовое в Docker (если `uv` или Python 3.14 не ставится)

Все бинарники (Python 3.14, `uv`, `pytest`, `ruff`, `basedpyright`, `alembic`) живут внутри контейнера `dev` (`/opt/venv`), а исходники монтируются с хоста — **OpenCode запускается локально** и правит те же файлы:

```bash
git clone -b main https://github.com/itpoohzhi/MoscowPythonPro.git ~/work/MoscowPythonPro
cd ~/work/MoscowPythonPro/workshop
test -f .env || cp .env.example .env && chmod 600 .env
docker compose up -d --build
docker compose exec dev alembic upgrade head
docker compose exec dev pytest -ra
docker compose exec dev ruff check .
docker compose exec dev basedpyright
docker compose exec dev python tools/verify_techlead_gate.py
```

Подробное описание микросервиса, учебных срезов и инструментов находится в [`workshop/README.md`](./workshop/README.md).

## Автор и контакты

- **Автор:** Алексей Жиряков
- **Telegram:** [@AlexeyZhi](https://t.me/AlexeyZhi)

## Лицензия и копирайт

[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)

`Copyright © 2026 Алексей Жиряков. Все права защищены.`

Материалы репозитория распространяются по лицензии **[Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)](./LICENSE)**:
- **BY (указание авторства):** обязательно указывать автора (Алексей Жиряков, [@AlexeyZhi](https://t.me/AlexeyZhi)).
- **NC (некоммерческое использование):** только для личного обучения; коммерческое использование, продажа и проведение курсов/тренингов без письменного разрешения автора запрещены.
- **ND (без производных произведений):** распространение переработанных версий запрещено.
