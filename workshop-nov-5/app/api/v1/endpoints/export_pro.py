"""Про-экспорт ссылок в JSON (транспортный слой): фильтр, поиск, пагинация.

Эндпоинт только валидирует HTTP-параметры через `Annotated[Query]` и вызывает
сервисный слой; DTO объявлены в `app/schemas/export.py`.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import ServiceDep
from app.schemas.export import ExportProResponse, ExportStatus

router = APIRouter(prefix="/export", tags=["export"])


@router.get(
    "/links/pro",
    response_model=ExportProResponse,
    summary="Про-экспорт ссылок с фильтрами и пагинацией",
)
async def export_links_pro(
    service: ServiceDep,
    status_filter: Annotated[ExportStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ExportProResponse:
    """Выгружает страницу ссылок JSON-схемой `ExportProResponse`."""
    return await service.export_links_pro(
        status_filter=status_filter, search=search, limit=limit, offset=offset
    )
