# Текущее состояние GSD-конвейера

- **Active State:** DONE
- **Feature Name:** link-tag-filter (LINK-43)
- **Current Wave:** Финал — панель техлидов 3× ACCEPT (раунд 2 + верификация раунда 3), merge-ready
- **Retry Count:** 1 / 3
- **Last Verified Checkpoint:**
  - Волна 1: миграция `alembic/versions/004_add_link_tags.py` + модель `tags` (одобрение архитектора
    зафиксировано в `specs/blast-radius.json:_architect_note`, ответ «Одобряю волну с миграцией», 2026-10-29;
    маятник upgrade→downgrade→upgrade = 0, `alembic check` = 0).
  - Волна 2: Red-Green реализация фильтра (Red: KeyError tags / полный список / 200 вместо 422);
    pytest -ra = 179 passed; ruff = 0; basedpyright = 0; verify_techlead_gate = ACCEPTED.
  - Панель техлидов (цикл 1): judge-1 REJECT (BLOCKER: LIKE-wildcard `_`), judge-2/3 ACCEPT (IMPORTANT);
    вердикт REJECT → бриф `handoff/panel-rework-brief.json` (RW-001..RW-006).
  - Цикл 2 (rework): RW-001 `autoescape=True` + Red-Green тест `test_underscore_tag_matches_nothing_else`;
    RW-002 фиксация ключей старого ответа; RW-005 `TAG_PATTERN` единый источник; RW-004/006 — долговые записи ниже.
  - Панель раунд 2: 3× ACCEPT (скептик дал новый IMPORTANT N1 — некорректное утверждение о guard);
    раунд 3: N1 CLOSED (commit `7d376b0`), судья подтверрил. Итог конвейера: **VERDICT READY**.
  - Отчёт приёмки: docs/reviews/link43_acceptance_report.md (раздел 1 — воспроизводимый след одобрения архитектора).

## Зарегистрированный техдолг LINK-43 (follow-ups)
- **Индексация тегов:** `links.tags` — JSON без индекса; предикат фильтрации `cast(tags AS VARCHAR) LIKE`
  выполняется полным сканом. Follow-up: миграция на `JSONB` + GIN `jsonb_path_ops` (PG17) либо отдельная
  таблица `link_tags(link_id, tag)` с индексом. (источник: панель judge-3:F2, judge-1:F7)
- **Пагинация тег-фильтра:** `list_tagged` имеет `offset`, но сервис/роутер его не пробрасывают; нет `total`.
  Образец — `list_pro`/`count_pro`. (judge-3:F6)
- **Протокол для Link-цепочки:** сервис импортирует `AsyncSession` напрямую; `docs/INDEX.md` обещает
  контракт через `app/core/protocols.py` — фактически протокол есть только для billing. Follow-up:
  `LinkRepositoryProtocol` (файл ядра — требует отдельного одобрения архитектора). (judge-3:F7)
- **Второй доменный стек без тегов:** `app/domain/link.py` / `link_repository.py` / `link_service.py` не
  знают про `tags` — расхождение зафиксировано осознанно (стек используется только юнит-тестами);
  при переезде/объединении стеков внести теги туда же. (judge-3:F4)
- **Red-Green регламент:** Red-фаза фиксируется в handoff/логе Оркестратора (для LINK-43: Red-вывод
  `KeyError 'tags'` / «полный список вместо отфильтрованного» / `tag='Uppercase' -> 200` в
  `handoff/coder.json`); для будущих задач — отдельный коммит Red-тестов либо запись Red-вывода
  в handoff/coder.json. (judge-2:F3)

## История состояний
- 2026-10-29: DONE — free-plan-link-limit-v3 (BILL-FREE01), Wave 5, Techlead Gate ACCEPTED (ruff, pytest 179 passed, plan_checker, ears_linter, verify_techlead_gate).
