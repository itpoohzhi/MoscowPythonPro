"""Контракты про-экспорта ссылок (DTO транспортного слоя `/export/links/pro`)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ExportStatus(StrEnum):
    """Строгий статус ссылки в выгрузке: активна, выключена или просрочена."""

    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"


class ExportProLinkItem(BaseModel):
    """Одна строка выгрузки ссылки с рассчитанным статусом."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    target_url: str
    clicks: int
    status: ExportStatus
    created_at: datetime
    expires_at: datetime | None


class ExportProResponse(BaseModel):
    """Страница выгрузки: элементы плюс метаданные среза пагинации."""

    total: int = Field(..., ge=0, description="Общее число ссылок под выбранными фильтрами")
    limit: int = Field(..., ge=1, le=1000, description="Размер страницы")
    offset: int = Field(..., ge=0, description="Смещение выборки")
    items: list[ExportProLinkItem]
