# Воркшоп MoscowPythonPro. Монолит, масштаб и приёмка

[![MoscowPython](./assets/moscowpython-logo.png)](./assets/moscowpython-logo.svg)

Каталог `workshop-nov-5/` на ветке `workshop-nov-5` и на тегах `snap-0` … `snap-6` — монолит `linksvc`
воркшопа MoscowPythonPro (проект сообщества MoscowPython) «От вайб-кодинга к профессиональной AI-разработке».

**Приложение едино для трёх дней и доступно с первого дня** (монолит links + analytics + billing).
Побайтово одинаковы во всех трёх днях шесть объектов приложения и окружения: `app/`, `alembic/`,
`alembic.ini`, `uv.lock`, `docker-compose.yml`, `.env.example`.
`pyproject.toml` един по зависимостям и настройкам инструментов и отличается только учебным порогом
покрытия `fail_under`: `50` в Дне 1 (лестница `50 → 60 → 80 → 85`) и `85` в Днях 2-3.
Каталог `tests/` (вместе с `agent-battle/`) содержит 179 тестов приложения и обвязки;
полный прогон `uv run pytest -ra` подтверждает точное число на финальном срезе `snap-6`.
Базовая лестница воркшопа растёт: **7 → 9 → 15** скилов. День 3 добавляет инструменты, которые ведут и принимают изменения монолита:
граф знаний, конвейер GSD, требования EARS, линтер слоёв, Blast Radius Guard и Techlead Gate.

В `.agents/skills/` лежат **28 каталогов процедурных скилов**: 15 скилов базовой лестницы воркшопа (7 из Дня 1, 2 из Дня 2 и 6 новых скилов Дня 3) и 13 инженерных скилов канонической библиотеки AI-SDLC. Дополнительно `teamlead-gate/SKILL.md` — каталог-алиас с полной копией `techlead-gate/SKILL.md` для одинаковой работы на macOS, Linux, WSL и Native Windows без `core.symlinks`.

## Скилы (`.agents/skills/`)

| День | Скил | Для чего |
| --- | --- | --- |
| 1 | `investigate-codebase`, `characterization-tests`, `tests-unit`, `tests-integration`, `database-migration`, `fastapi-feature`, `safe-refactoring` | Базовые скилы одиночного инженера |
| 2 | `small-fix`, `pipeline` | Точечная правка и конвейер Coder → Reviewer → Gate |
| **3** | `monolith-knowledge-graph` | База знаний `docs/INDEX.md` и AST-граф зависимостей, Scoped Retrieval вместо чтения всего кода |
| **3** | `open-gsd-pipeline` | Задача волнами через `.planning/`: состояние, требования, дорожная карта |
| **3** | `spec-kit-ears` | Требования в синтаксисе EARS (`specs/billing-ears.md`) и их линтер |
| **3** | `architecture-layers-linter` | Границы слоёв schemas → core → services → api проверяются по AST |
| **3** | `blast-radius-guard` | Бюджет изменений (до 7 файлов) и замороженное ядро (`CODEOWNERS`) |
| **3** | `techlead-gate` | Приёмка: 5 проверок подряд одной командой |

## Что лежит в каталоге

| Путь | Назначение |
| --- | --- |
| `app/` | Единое приложение: `core/` (настройки, логирование, протоколы), `schemas/`, `services/`, `api/`, `db/`, `models/`, `repositories/`, `domain/` |
| `app/schemas/billing.py`, `app/core/protocols.py`, `app/services/billing.py`, `app/api/billing.py` | Домен Billing (те же файлы лежат в Днях 1-2) |
| `alembic/` | Четыре миграции: `001_initial_links`, `002_add_analytics_events`, `003_add_created_at_idx`, `004_add_link_tags` |
| `docs/module-map.md` | Карта модулей цепочки создания ссылки (вход скила `small-fix`), из Дня 2 |
| `docs/INDEX.md`, `docs/domains/*.md` | Карта монолита и спецификации доменов |
| `.planning/` | `STATE.md`, `REQUIREMENTS.md`, `ROADMAP.md` конвейера GSD |
| `specs/` | `billing-ears.md` (EARS), `blast-radius.json` (бюджет изменений) |
| `tools/` | Верификаторы и вспомогательные утилиты (таблица ниже) |
| `tests/` | `unit/`, `integration/`, `characterization/`, `flat_api/` — 179 тестов монолита и обвязки на финальном срезе; SQLite in-memory, плюс `agent-battle/` для атомарного счётчика |
| `.github/CODEOWNERS`, `.open-codeignore`, `.pre-commit-config.yaml` | Замороженное ядро, исключения для агента, локальные хуки |

## Запуск и проверки

Нужны Python 3.14 и [uv](https://docs.astral.sh/uv/). Postgres для тестов не нужен.
Команды выполняйте через `uv run`: верификаторы вызывают `python3` и `pytest` из окружения проекта.

```bash
cd ~/work/MoscowPythonPro/workshop-nov-5   # на ветке workshop-nov-5 или на теге snap-N
uv sync
uv run ruff check .
uv run pytest -q
uv run python tools/plan_checker.py
uv run python tools/ears_linter.py
uv run python tools/verify_techlead_gate.py
```

| Утилита | Что проверяет или строит |
| --- | --- |
| `tools/verify_kb_sync.py` | Файлы из `docs/INDEX.md` существуют, индекс не длиннее 100 строк |
| `tools/build_dependency_graph.py --check-cycles` | В графе импортов нет циклов |
| `tools/verify_architecture_layers.py` | Нет запрещённых импортов между слоями |
| `tools/verify_blast_radius.py` | Изменено не больше 7 файлов, замороженное ядро не тронуто (по `git status`) |
| `tools/verify_techlead_gate.py` | Пять стадий: KB, AST-граф, границы слоёв, Blast Radius и `pytest tests/unit tests/integration` |
| `tools/plan_checker.py`, `tools/gsd_fsm_runner.py` | Проверка и переходы состояния в `.planning/STATE.md` |
| `tools/ears_linter.py` | Требования в `specs/` соответствуют EARS |
| `tools/scoped_retrieval.py`, `build_call_graph.py`, `generate_repomap.py`, `compress_handoff.py` | Минимальный контекст для агента |
| `tools/benchmark_billing.py` | Замер задержки `POST /billing/charges/click` через TestClient |

## Контрольные срезы `snap-0` … `snap-6`

Теги лежат на истории ветки `workshop-nov-5`. Перейти к срезу: `git checkout snap-3`
или `./tools/restore_checkpoint.sh snap-3`.
Вернуться: `git checkout workshop-nov-5`. На каждом срезе проходят `uv run pytest -q` и те верификаторы,
которые уже есть на этом срезе.

Приложение во всех срезах одно и то же; растёт набор скилов и обвязки.

| Тег | Что добавлено | Скилов |
| --- | --- | --- |
| `snap-0` | Единое приложение (links, analytics, billing) и скилы Дней 1-2 | 9 |
| `snap-1` | База знаний: `docs/INDEX.md`, `docs/domains/`, `verify_kb_sync` | 9 |
| `snap-2` | AST-граф, Scoped Retrieval, скил `monolith-knowledge-graph` | 10 |
| `snap-3` | Конвейер GSD (`.planning/`) и требования EARS: `open-gsd-pipeline`, `spec-kit-ears`, `ears_linter` | 12 |
| `snap-4` | Линтер слоёв: `verify_architecture_layers`, `architecture-layers-linter`, pre-commit | 13 |
| `snap-5` | Blast Radius Guard: `specs/blast-radius.json`, `CODEOWNERS`, `blast-radius-guard` | 14 |
| `snap-6` | Techlead Gate: `verify_techlead_gate`, скил `techlead-gate`, контрольные утилиты | 15 |

## Известные ограничения

- Приложение объединяет baseline Дня 1 (доменный слой `app/domain/`, плоские маршруты `/links`),
  контур Дня 2 (редирект `/{code}`, disable/enable) и монолит Дня 3 (`/api/v1/...`, analytics,
  billing). Сравнение `expires_at` учитывает наивное время SQLite, SSRF-валидатор лежит в
  `app/schemas/validators.py` (`app/core/security.py` реэкспортирует его), чтобы схемы не
  импортировали `app.core`.
- `app/api/links.py`, `app/schemas/links.py`, `app/services/links.py` — тонкие фасады над
  `link.py` и `app/api/v1/endpoints/links.py`: на них ссылается `docs/INDEX.md` (со `snap-1`);
  `app/repo.py`, `app/service.py`, `app/models_flat.py` — функциональные фасады имён Дня 2.
- `app/services/link_service.py` + `app/repositories/link_repository.py` — доменный сервис
  Дня 1 (протокол репозитория, атомарный счётчик, `agent-battle/`), независимый от HTTP-слоя.
- Репозиторий биллинга в `app/api/billing.py` хранит данные в памяти процесса.
