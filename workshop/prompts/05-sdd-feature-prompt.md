Задача (SDD): реализовать фичу `LINK-44` — продление срока жизни короткой ссылки (`POST /api/v1/links/{short_code}/extend-ttl`).

РАБОТАЙ СТРОГО ПО СКИЛАМ И КОНТРАКТАМ ПРОЕКТА:
1. Прочитай карту архитектуры `docs/INDEX.md`, правила `AGENTS.md` и рубрику приёмки `docs/gate-rubric.md`.
2. **Этап 1 — Постановка задачи по SDD (скилл `.agents/skills/spec-kit-ears/SKILL.md`):**
   Сначала создай на диске компактную спецификацию `specs/LINK-44-extend-ttl-ears.md` (2–5 КБ) в синтаксисе EARS (`СИСТЕМА ДОЛЖНА`, `КОГДА`, `ПОКА`, `ЕСЛИ ... ТО`) со следующими обязательными блоками:
   - **Blast Radius:** не более 6 файлов (`specs/LINK-44-extend-ttl-ears.md`, схемы, репозиторий, сервис, роутер `app/api/v1/endpoints/links.py`, тесты `tests/integration/test_extend_ttl.py`). Замороженные файлы (`app/main.py`, `app/core/config.py`, `app/core/security.py`, `AGENTS.md`, `pyproject.toml`, `uv.lock`, существующие тесты) — НЕ ТРОГАТЬ.
   - **Контракт API и DTO (Pydantic v2):**
     - `POST /api/v1/links/{short_code}/extend-ttl`
     - Вход `ExtendTtlRequest`: `extend_hours: int = Field(ge=1, le=8760)` (от 1 часа до 1 года; `<= 0` и `> 8760` → `422 Unprocessable Entity`, защита от overflow даты).
     - Выход `ExtendTtlResponse`: `short_code: str`, `expires_at: datetime` (строго timezone-aware `UTC`), `disabled: bool`.
   - **Бизнес-правила и негативные сценарии (EARS):**
     - `КОГДА` ссылка активна (`disabled=False`) и `expires_at` в будущем — `СИСТЕМА ДОЛЖНА` прибавить `timedelta(hours=extend_hours)` к текущему `expires_at` (в `UTC`).
     - `КОГДА` ссылка активна, но `expires_at is None` или уже в прошлом (`<= now(UTC)`) — `СИСТЕМА ДОЛЖНА` установить `expires_at = now(UTC) + timedelta(hours=extend_hours)`.
     - `ЕСЛИ` ссылка не найдена — `ТО СИСТЕМА ДОЛЖНА` вернуть `404 Not Found` (`{"detail": "Link not found"}`).
     - `ПОКА` ссылка отключена (`disabled=True`) — `СИСТЕМА ДОЛЖНА` отклонять продление со статусом `409 Conflict` (`{"detail": "Cannot extend TTL of disabled link"}`), не изменяя `expires_at`.
   - **NFR и слои:** слои `schemas -> repositories -> services -> api` (без SQL в роутере), строго `datetime.now(timezone.utc)`, без утечки `target_url`/токенов в логах (CWE-532), колонка `expires_at` уже существует в `app/models/link.py` (схему БД не ломать).
   - **Definition of Done (CLI-команды):** `uv run ruff check app tests`, `uv run basedpyright`, `uv run pytest tests/integration/test_extend_ttl.py -v`, `uv run pytest tests/unit -q`.
3. **Этап 2 — Реализация по спеке (скилл `.agents/skills/feature/SKILL.md`):**
   - Сначала напиши интеграционные тесты `tests/integration/test_extend_ttl.py` по всем пунктам EARS (успешное продление активной ссылки, продление истёкшей/бессрочной от `now(UTC)`, `404`, `409` для `disabled=True`, `422` для `0`, `-5`, `8761`) и зафиксируй Red-фазу.
   - Затем реализуй по слоям (схема → репозиторий → сервис → роутер `app/api/v1/endpoints/links.py`) без SQL в хэндлере.
   - Прогони все команды DoD и добейся `exit 0`.
4. В конце выведи короткий отчёт: путь к спеке, список изменённых файлов (`git diff --stat`) и фактические коды выхода `ruff`, `basedpyright` и `pytest`.
