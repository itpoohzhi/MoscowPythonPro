import csv
import hashlib
import io
import secrets
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.link import Link
from app.repositories.link import LinkRepository
from app.schemas.export import ExportProLinkItem, ExportProResponse, ExportStatus
from app.schemas.link import (
    LinkBulkCreateItem,
    LinkBulkCreateResponse,
    LinkCreate,
    LinkResponse,
    LinkStats,
)


class LinkServiceError(Exception):
    """Базовое исключение сервисного слоя."""

    pass


class LinkNotFoundError(LinkServiceError):
    """Исключение: ссылка не найдена."""

    pass


class LinkInactiveError(LinkServiceError):
    """Исключение: ссылка деактивирована."""

    pass


class LinkExpiredError(LinkServiceError):
    """Исключение: срок действия ссылки истек."""

    pass


class ShortCodeConflictError(LinkServiceError):
    """Исключение: короткий код уже занят."""

    pass


CSV_EXPORT_HEADER = (
    "id",
    "short_code",
    "target_url",
    "clicks",
    "disabled",
    "created_at",
    "expires_at",
)


class LinkService:
    """Сервис управления жизненным циклом ссылок."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LinkRepository(session)

    @staticmethod
    def _generate_code(url: str, attempt: int = 0) -> str:
        """Детерминированная генерация короткого Base62-кода с солью попытки."""
        salt = secrets.token_hex(2) if attempt > 0 else ""
        raw = f"{url}:{salt}:{attempt}".encode()
        digest = hashlib.sha256(raw).hexdigest()
        alphabet = "23456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
        num = int(digest[:10], 16)
        code = ""
        while num > 0 and len(code) < 7:
            num, rem = divmod(num, len(alphabet))
            code += alphabet[rem]
        return code.ljust(6, "x")

    async def create_link(self, data: LinkCreate) -> Link:
        """Создание новой короткой ссылки с валидацией коллизий."""
        expires_at = None
        if data.ttl_seconds is not None:
            expires_at = datetime.now(UTC) + timedelta(seconds=data.ttl_seconds)

        if data.custom_code:
            existing = await self._repo.get_by_code(data.custom_code)
            if existing is not None:
                logger.warn("custom_code_conflict", code=data.custom_code)
                raise ShortCodeConflictError(f"Код '{data.custom_code}' уже используется")
            short_code = data.custom_code
        else:
            short_code = ""
            for attempt in range(5):
                candidate = self._generate_code(data.original_url, attempt)
                if await self._repo.get_by_code(candidate) is None:
                    short_code = candidate
                    break
            if not short_code:
                raise LinkServiceError("Не удалось сгенерировать уникальный код ссылки")

        link = Link(
            short_code=short_code,
            target_url=data.original_url,
            expires_at=expires_at,
            disabled=False,
            clicks=0,
            tags=data.tags,
        )
        saved = await self._repo.create(link)
        logger.info("link_created", short_code=saved.short_code, id=saved.id)
        return saved

    async def resolve_link(self, short_code: str) -> str:
        """Разрешение короткого кода в оригинальный URL с проверкой активности."""
        link = await self._repo.get_by_code(short_code)
        if link is None:
            raise LinkNotFoundError(f"Ссылка с кодом '{short_code}' не найдена")
        if not link.is_active:
            raise LinkInactiveError(f"Ссылка '{short_code}' деактивирована")
        if link.is_expired:
            raise LinkExpiredError(f"Срок действия ссылки '{short_code}' истек")

        await self._repo.increment_clicks(link.id)
        logger.info("link_resolved", short_code=short_code, clicks=link.clicks + 1)
        return link.target_url

    async def get_stats(self, short_code: str) -> LinkStats:
        """Получение статистики переходов по ссылке."""
        link = await self._repo.get_by_code(short_code)
        if link is None:
            raise LinkNotFoundError(f"Ссылка с кодом '{short_code}' не найдена")
        return LinkStats.model_validate(link)

    async def get_link(self, short_code: str) -> Link:
        """Получение ссылки по коду (без побочных эффектов)."""
        link = await self._repo.get_by_code(short_code)
        if link is None:
            raise LinkNotFoundError(f"Ссылка с кодом '{short_code}' не найдена")
        return link

    async def list_links(self, limit: int = 100, tag: str | None = None) -> Sequence[Link]:
        """Список ссылок: новые первыми; при `tag` — только содержащие тег."""
        if tag is None:
            return await self._repo.list_all(limit=limit)
        return await self._repo.list_tagged(tag, limit=limit)

    async def export_links_csv(self, limit: int = 10_000) -> str:
        """Экспорт всех ссылок сервиса в CSV (это и есть файл отдачи эндпоинта)."""
        links = await self._repo.list_all(limit=limit)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(CSV_EXPORT_HEADER)
        for link in links:
            writer.writerow(
                (
                    link.id,
                    link.short_code,
                    link.target_url,
                    link.clicks,
                    "true" if link.disabled else "false",
                    link.created_at.isoformat(),
                    link.expires_at.isoformat() if link.expires_at else "",
                )
            )
        logger.info("links_exported", count=len(links))
        return buffer.getvalue()

    async def export_links_pro(
        self,
        *,
        status_filter: ExportStatus | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> ExportProResponse:
        """Про-экспорт ссылок: фильтр по статусу, поиск, пагинация и общий total."""
        links = await self._repo.list_pro(
            status_filter=status_filter, search=search, limit=limit, offset=offset
        )
        total = await self._repo.count_pro(status_filter=status_filter, search=search)
        items = [ExportProLinkItem.model_validate(link) for link in links]
        logger.info("links_exported_pro", total=total, returned=len(items))
        return ExportProResponse(total=total, limit=limit, offset=offset, items=items)

    async def disable_link(self, short_code: str) -> Link:
        """Деактивация короткой ссылки."""
        link = await self._repo.set_active(short_code, is_active=False)
        if link is None:
            raise LinkNotFoundError(f"Ссылка с кодом '{short_code}' не найдена")
        logger.info("link_disabled", short_code=short_code)
        return link

    async def enable_link(self, short_code: str) -> Link:
        """Включение ранее деактивированной ссылки."""
        link = await self._repo.set_active(short_code, is_active=True)
        if link is None:
            raise LinkNotFoundError(f"Ссылка с кодом '{short_code}' не найдена")
        logger.info("link_enabled", short_code=short_code)
        return link

    async def bulk_create_links(self, items: list[LinkBulkCreateItem]) -> LinkBulkCreateResponse:
        """Пакетное создание нескольких ссылок в рамках одной транзакции."""
        created: list[LinkResponse] = []
        for item in items:
            dto = LinkCreate(
                original_url=item.original_url,
                custom_code=item.custom_code,
                ttl_seconds=item.ttl_seconds,
            )
            model = await self.create_link(dto)
            created.append(LinkResponse.model_validate(model))
        return LinkBulkCreateResponse(created_count=len(created), links=created)
