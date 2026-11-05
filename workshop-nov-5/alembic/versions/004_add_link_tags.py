"""Добавление колонки `tags` в таблицу `links` (фича фильтрации по тегам, LINK-43).

Теги хранятся в виде JSON-массива строк; значение по умолчанию — пустой массив,
старые строки и старые контракты не затрагиваются.

Revision ID: 004_add_link_tags
Revises: 003_add_created_at_idx
"""

import sqlalchemy as sa
from alembic import op

revision: str = "004_add_link_tags"
down_revision: str | None = "003_add_created_at_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавление колонки `tags` с непустым значением по умолчанию."""
    op.add_column(
        "links",
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    """Полный откат: колонка `tags` удаляется (никаких пустых pass)."""
    op.drop_column("links", "tags")
