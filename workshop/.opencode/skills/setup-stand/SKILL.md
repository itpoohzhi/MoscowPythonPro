---
name: setup-stand
description: "Подготовка рабочего стенда: скачивание ветки main и тегов с origin, переключение на main, развёртывание .env, uv sync (Python 3.14 only-managed) и контрольный прогон pytest."
---

# Скил: setup-stand (Подготовка рабочего стенда)

## Процедура
1. Стянуть ветку `main` и теги контрольных точек с сервера:
   ```bash
   git fetch origin main --tags
   ```
2. Переключиться на рабочую ветку `main`:
   ```bash
   git checkout -f main
   ```
3. Создать локальный файл конфигурации `.env` из шаблона при отсутствии:
   ```bash
   test -f .env || cp .env.example .env
   ```
4. Синхронизировать виртуальное окружение и зависимости на стабильном Python 3.14:
   ```bash
   uv sync --python 3.14 --python-preference only-managed
   ```
5. Выполнить проверочный запуск тестов:
   ```bash
   uv run pytest tests/unit -q
   ```

## Критерий готовности (DoD)
- Текущая ветка строго `main`.
- Теги `snap-0` … `snap-6` доступны локально.
- Все юнит-тесты завершаются успешно (код 0).
