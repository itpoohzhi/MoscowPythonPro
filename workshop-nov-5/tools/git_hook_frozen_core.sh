#!/usr/bin/env bash
set -e

FROZEN_FILES=("app/core/config.py" "app/core/security.py" "app/main.py")

CHANGED=$(git diff --cached --name-only)
PREFIX=$(git rev-parse --show-prefix 2>/dev/null || echo "")

for file in $CHANGED; do
    if [ -n "$PREFIX" ]; then
        file=${file#"$PREFIX"}
    else
        file=${file#"workshop-nov-5/"}
    fi
    for frozen in "${FROZEN_FILES[@]}"; do
        if [ "$file" == "$frozen" ]; then
            echo "🚨 ОШИБКА: Попытка коммита замороженного файла ядра: $file"
            echo "   Файлы ядра защищены от модификации агентами!"
            echo "   Требуется ручное подтверждение Архитектора."
            exit 1
        fi
    done
done

echo "✅ Проверка Frozen Core пройдена (защищенные файлы не затронуты)."
exit 0
