from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TypeVar

from sqlalchemy import Select, String, cast, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.schemas.export import ExportStatus

_EntityT = TypeVar("_EntityT")


class LinkRepository:
    """Асинхронный репозиторий для сущности Link."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_code(self, short_code: str) -> Link | None:
        """Поиск ссылки по короткому коду."""
        stmt = select(Link).where(Link.short_code == short_code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, link_id: int) -> Link | None:
        """Поиск ссылки по первичному ключу."""
        return await self._session.get(Link, link_id)

    async def create(self, link: Link) -> Link:
        """Сохранение новой ссылки в сессии."""
        self._session.add(link)
        await self._session.flush()
        await self._session.refresh(link)
        return link

    async def bulk_create(self, links: list[Link]) -> list[Link]:
        """Пакетное добавление сущностей."""
        self._session.add_all(links)
        await self._session.flush()
        for link in links:
            await self._session.refresh(link)
        return links

    async def increment_clicks(self, link_id: int) -> None:
        """Атомарный инкремент счетчика переходов."""
        stmt = update(Link).where(Link.id == link_id).values(clicks=Link.clicks + 1)
        await self._session.execute(stmt)

    async def set_active(self, short_code: str, is_active: bool) -> Link | None:
        """Изменение статуса активности ссылки."""
        link = await self.get_by_code(short_code)
        if link:
            link.is_active = is_active
            await self._session.flush()
            await self._session.refresh(link)
        return link

    async def list_all(self, limit: int = 100, offset: int = 0) -> Sequence[Link]:
        """Все ссылки (новые первыми) с пагинацией."""
        stmt = select(Link).order_by(Link.id.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    def _pro_filters(
        stmt: Select[tuple[_EntityT]],
        status_filter: ExportStatus | None,
        search: str | None,
        now_utc: datetime,
    ) -> Select[tuple[_EntityT]]:
        """Безопасные фильтры про-экспорта: статус и подстрока URL/кода."""
        if status_filter is ExportStatus.ACTIVE:
            stmt = stmt.where(Link.expires_at.is_(None) | (Link.expires_at > now_utc))
            stmt = stmt.where(Link.disabled.is_(False))
        elif status_filter is ExportStatus.DISABLED:
            stmt = stmt.where(Link.disabled.is_(True))
        elif status_filter is ExportStatus.EXPIRED:
            stmt = stmt.where(
                Link.disabled.is_(False)
                & Link.expires_at.is_not(None)
                & (Link.expires_at <= now_utc)
            )
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(Link.target_url.ilike(pattern) | Link.short_code.ilike(pattern))
        return stmt

    async def list_pro(
        self,
        *,
        status_filter: ExportStatus | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Link]:
        """Все ссылки (новые первыми) с фильтром статуса, поиском и пагинацией."""
        stmt = select(Link).order_by(Link.id.desc())
        stmt = self._pro_filters(stmt, status_filter, search, datetime.now(UTC))
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count_pro(
        self,
        *,
        status_filter: ExportStatus | None = None,
        search: str | None = None,
    ) -> int:
        """Полное число ссылок, попадающее под фильтры про-экспорта."""
        stmt = select(func.count()).select_from(Link)
        stmt = self._pro_filters(stmt, status_filter, search, datetime.now(UTC))
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_active(self, limit: int = 50, offset: int = 0) -> Sequence[Link]:
        """Список активных ссылок с пагинацией."""
        stmt = (
            select(Link)
            .where(Link.is_active == True)  # noqa: E712
            .order_by(Link.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_tagged(self, tag: str, *, limit: int = 100, offset: int = 0) -> Sequence[Link]:
        """Ссылки, чей массив `tags` содержит тег (новые первыми), с пагинацией.

        Предикат переносим между PostgreSQL и SQLite: JSON-колонка приводится
        к строке и ищется подстрока `"tag"` (кавычки исключают ложные вхождения
        вида `mytag` при поиске `tag`). Нормализация регистра выполняется не
        схемой: теги валидируются как есть (`^[a-z0-9_-]{2,32}$`), поэтому
        данные, записанные в обход API, могут фильтроваться по-разному в PG17
        и SQLite. Wildcard-джокеры (`_`, `%`) экранируются `autoescape=True`.
        """
        stmt = (
            select(Link)
            .where(cast(Link.tags, String).contains(f'"{tag}"', autoescape=True))
            .order_by(Link.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
