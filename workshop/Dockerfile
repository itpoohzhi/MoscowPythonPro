# syntax=docker/dockerfile:1
FROM python:3.14

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_NO_SYNC=1 \
    PATH="/opt/venv/bin:/usr/local/bin:${PATH}"

# Готовый бинарный wheel uv из PyPI (без apt-get, без ghcr.io, без компиляции)
RUN pip install --no-cache-dir uv \
    && git config --system --add safe.directory '*'

# Ставим все зависимости проекта в /opt/venv внутри образа (вне монтируемого каталога кода)
WORKDIR /tmp/deps
COPY pyproject.toml uv.lock ./
RUN UV_NO_SYNC=0 uv sync --frozen --no-install-project --no-editable

WORKDIR /repo/workshop
CMD ["sleep", "infinity"]
