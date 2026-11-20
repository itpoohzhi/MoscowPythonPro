---
name: teamlead-gate
description: >-
  Скилл автономной оркестрации тимлида (Teamlead Gate): ведёт задачу от
  спецификации до проверяемого вердикта без ручного запуска 4 отдельных шагов.
  Управляет полным циклом Кодер (feature/rework) -> CODE_GATE -> Панель
  техлидов (3 разные flash-модели OpenCode Go) -> Суммаризатор -> Rework
  (до 5 циклов) либо проводит приёмку уже готового diff.
---

# Скил: teamlead-gate (Автономный Оркестратор тимлида)

Скилл задаёт роль **Оркестратора (Тимлида)** в конвейере разработки `linksvc`. Вместо того чтобы вручную запускать 4 отдельных шага (Кодер → CODE_GATE → Суммаризатор + Rework → Панель техлидов), разработчик передаёт задачу одной командой этому скиллу — Оркестратор сам координирует все роли в изолированных процессах и доводит ветку до проверяемого вердикта на диске.

*(Не путать с детерминированным скриптом-шлюзом `.agents/skills/techlead-gate/SKILL.md`: `techlead-gate` запускает только локальные проверки `tools/verify_techlead_gate.py`, а `teamlead-gate` оркестрирует весь многоагентный цикл с Кодером и Панелью техлидов.)*

## Режимы работы

1. **Режим A — Полная автономная оркестрация (по умолчанию для новой задачи/спеки):**
   `INIT → Кодер (Цикл 1: feature) → CODE_GATE → Панель техлидов (3 модели) → [при REJECT: panel-rework-summarizer → Кодер (Циклы 2..5: rework) → повтор]` → `READY | ESCALATE`.
2. **Режим B — Приёмка готового diff (`gate-only`, если код уже написан):**
   пропуск Цикла 1 Кодера, сразу `CODE_GATE → Панель техлидов (3 модели) → вердикт` (`.ai-team/verdict.md`).

## Нерушимые правила Оркестратора

1. **Режим `SOURCE READ-ONLY`:** Оркестратор **не пишет** продуктовый и тестовый код и не выносит оценок за судей. Разрешена запись только служебных артефактов прохода в `.ai-team/` и `handoff/`.
2. **Запрет самопроверки:** Кодер, каждый судья Панели и Суммаризатор запускаются отдельными свежими процессами `opencode run ... < /dev/null` без `--continue` и `--session`.
3. **Никакой веры на слово:** статус каждой фазы подтверждается кодом возврата команды и артефактами на диске (`handoff/coder-NN.json`, `.ai-team/code-gate.json`, `.ai-team/panel/*`, `.ai-team/verdict.md`).
4. **Защита от правки кода судьями:** все судьи работают в режиме `STRICT READ-ONLY` (ответ в `stdout`, файлы в `.ai-team/panel/` сохраняет Оркестратор). Любая модификация дерева проекта вне `.ai-team/` и `handoff/` во время раунда судьи → немедленный `ESCALATE`.
5. **Лимит циклов:** максимум **5 циклов** Кодера (Цикл 1 — `feature`, Циклы 2..5 — `rework`). Шестого цикла нет; при исчерпании лимита или техническом сбое — `ESCALATE` человеку.
6. **Запрет правки защищённых файлов:** `AGENTS.md`, `pyproject.toml`, `uv.lock`, спека и скиллы не модифицируются Кодером.

## Матрица ролей и моделей (OpenCode Go, 3 независимых семейства)

| Роль | Скилл / Процедура | Модель по умолчанию (OpenCode Go) | Переменная переопределения | Доступ |
|---|---|---|---|---|
| **Coder (Цикл 1)** | `.agents/skills/feature/SKILL.md` | `opencode-go/deepseek-v4.1-flash` | `OPENCODE_MODEL_CODER` | `WRITE` (Blast Radius) |
| **Coder (Циклы 2..5)** | `.agents/skills/rework/SKILL.md` | `opencode-go/deepseek-v4.1-flash` | `OPENCODE_MODEL_CODER` | `WRITE` (только `RW-NNN`) |
| **CODE_GATE** | `tools/verify_techlead_gate.py` + `ruff`/`basedpyright`/`alembic`/`pytest`/`mutate_probe` | Детерминированные скрипты (без LLM) | — | `EXEC` (read-only к коду) |
| **Judge-1 (Скептик)** | `.agents/skills/teamlead-panel/SKILL.md` | `opencode-go/deepseek-v4.1-flash` | `OPENCODE_MODEL_JUDGE1` | `STRICT READ-ONLY` |
| **Judge-2 (Реалист)** | `.agents/skills/teamlead-panel/SKILL.md` | `opencode-go/glm-5.3-flash` | `OPENCODE_MODEL_JUDGE2` | `STRICT READ-ONLY` |
| **Judge-3 (Визионер)** | `.agents/skills/teamlead-panel/SKILL.md` | `opencode-go/qwen3.8-flash` | `OPENCODE_MODEL_JUDGE3` | `STRICT READ-ONLY` |
| **Summarizer** | `panel-rework-summarizer` (`teamlead-panel`) | `opencode-go/glm-5.3-flash` | `OPENCODE_MODEL_SUMMARIZER` | `STRICT READ-ONLY` |

При временной недоступности одной из моделей OpenCode Go допустимы проверенные flash-замены: `opencode-go/minimax-m3.1-flash`, `opencode-go/mimo-v2.6-flash`. Единый override для всех ролей задаётся через `OPENCODE_MODEL` / `--model`.

## Алгоритм исполнения (Конечный автомат)

```text
INIT (спека + ветка + цикл=1)
  ├─ [Режим A] → CODER (feature) → handoff/coder-01.json + .ai-team/handoff-coder.md
  └─ [Режим B] → сразу CODE_GATE
        │
        ▼
   CODE_GATE (ruff, basedpyright, alembic, pytest, Blast Radius, verify_kb_sync)
     ├─ FAIL → handoff/gate-failure-brief.json (CG-NNN) → CODER (rework, цикл+1)
     └─ PASS → .ai-team/code-gate.json
                 │
                 ▼
          ПАНЕЛЬ ТЕХЛИДОВ (3 разные модели OpenCode Go, STRICT READ-ONLY)
            ├─ ACCEPT (3/3, нет BLOCKER/IMPORTANT) → scripts/generate_proof.py → Вердикт: READY (exit 0)
            ├─ REJECT → panel-rework-summarizer → handoff/panel-rework-brief.json (RW-NNN)
            │           ├─ цикл < 5 → CODER (rework, цикл+1) → CODE_GATE
            │           └─ цикл == 5 → Вердикт: ESCALATE (exit 2)
            └─ Сбой транспорта / кворума / read-only violation → Вердикт: ESCALATE (exit 2)
```

### Фаза 0. Preflight
1. Проверить корень проекта (`git rev-parse --show-toplevel`), текущую ветку (не `main` для разработки), наличие целевой спецификации (`specs/*.md`), рубрики `docs/gate-rubric.md` и `AGENTS.md`.
2. Создать `mkdir -p .ai-team/panel handoff`.
3. Определить режим: если в задаче требуется реализация фичи по спеке (Режим A) — начинать с Фазы 1; если передан запрос «проведи приёмку уже готовой задачи» (Режим B) — переходить к Фазе 2.

### Фаза 1. Кодер (Цикл 1 — только в Режиме A)
1. Запустить изолированный процесс Кодера со скиллом `.agents/skills/feature/SKILL.md`:
   ```bash
   opencode run --auto -m "${OPENCODE_MODEL_CODER:-${OPENCODE_MODEL:-opencode-go/deepseek-v4.1-flash}}" \
     "По скилу .agents/skills/feature/SKILL.md реализуй задачу <TASK_ID> по спеке <SPEC_PATH>. Соблюдай Blast Radius и Red-Green TDD. Сдай handoff/coder-01.json и .ai-team/handoff-coder.md." < /dev/null
   ```
2. Проверить формат handoff валидатором: `uv run python scripts/validate_handoff.py handoff/coder-01.json .ai-team/handoff-coder.md`.

### Фаза 2. Детерминированный CODE_GATE
1. Лично выполнить проверки (не доверяя отчёту Кодера):
   - `uv run python scripts/orchestrate_pipeline.py --run-gates` (или по шагам: `tools/verify_kb_sync.py`, `tools/verify_architecture_layers.py`, `tools/verify_blast_radius.py`, `uv run ruff check app tests`, `uv run basedpyright`, `uv run pytest -q`).
2. Зафиксировать свидетельство в `.ai-team/code-gate.json`.
3. Если любой гейт красный: сформировать `handoff/gate-failure-brief.json` (`CG-001`…) и вернуть задачу Кодеру в Фазу 4 (`rework`) без вызова Панели судей.

### Фаза 3. Панель техлидов (3 разные модели)
1. Вызвать трёх судей строго отдельными свежими процессами `opencode run -m <model> --format json "<brief>" < /dev/null` по процедуре `.agents/skills/teamlead-panel/SKILL.md` (для полного 15-вызовного протокола консенсус-дебатов `R1 → D1 → D2 → D3 → FREEZE → C1` — см. `.agents/skills/teamlead-panel/references/consensus-debate.md` и `scripts/generate_proof.py`; для ускоренного цикла оркестратора — 3 параллельных судьи в `.ai-team/panel/judge-{1,2,3}.json` и проверка `scripts/orchestrate_pipeline.py --check`).
2. Проверить, что `git status --short` не содержит посторонних правок кода от судей.
3. Посчитать итог детерминированно скриптом (`scripts/generate_proof.py` либо `scripts/orchestrate_pipeline.py --check`) и записать `.ai-team/verdict.md`.

### Фаза 4. Суммаризатор и цикл доработки `rework` (Циклы 2..5)
1. При `REJECT`: запустить `panel-rework-summarizer` на модели `${OPENCODE_MODEL_SUMMARIZER:-opencode-go/glm-5.3-flash}` (STRICT READ-ONLY) и сохранить `handoff/panel-rework-brief.json` (`RW-001`…).
2. Проверить бриф: `uv run python scripts/validate_handoff.py handoff/panel-rework-brief.json`.
3. Запустить Кодера в свежем процессе со скиллом `.agents/skills/rework/SKILL.md` строго по пунктам `RW-NNN` (или `CG-NNN` при сбое CODE_GATE):
   ```bash
   opencode run --auto -m "${OPENCODE_MODEL_CODER:-${OPENCODE_MODEL:-opencode-go/deepseek-v4.1-flash}}" \
     "По скилу .agents/skills/rework/SKILL.md выполни Цикл <N> по задачам из handoff/panel-rework-brief.json для спеки <SPEC_PATH>. Сдай handoff/coder-0<N>.json и обнови .ai-team/handoff-coder.md." < /dev/null
   ```
4. Повторить Фазу 2 (`CODE_GATE`) и Фазу 3 (`Панель техлидов`). После 5 неудачных циклов остановиться с `Вердикт: ESCALATE`.

## Выходные артефакты и Definition of Done (DoD)

- [ ] Все роли запущены отдельными свежими процессами (`< /dev/null`, без `--continue`/`--session`).
- [ ] Коллегия судей состоит из 3 разных flash-моделей OpenCode Go (`deepseek-v4.1-flash`, `glm-5.3-flash`, `qwen3.8-flash` или явных `OPENCODE_MODEL_JUDGE1..3`).
- [ ] `.ai-team/code-gate.json` зелёный (все шаги `exit_code == 0`), Blast Radius и база знаний не нарушены.
- [ ] Первая строка `.ai-team/verdict.md` — ровно `Вердикт: READY`, `Вердикт: REWORK` или `Вердикт: ESCALATE`, подтверждена детерминированным чекером (`scripts/orchestrate_pipeline.py --check` / `scripts/generate_proof.py`).
- [ ] В финальном отчёте приведены фактические команды, коды выхода, модели судей и список затронутых файлов.
