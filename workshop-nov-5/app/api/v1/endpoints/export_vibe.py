"""Экспорт всех ссылок сервиса в CSV-файл (транспортный слой).

Эндпоинт только принимает HTTP-запрос и упаковывает результат сервисного слоя
в файл-отдачу; вся логика выгрузки — в `app/services/link.py`.
"""

from fastapi import APIRouter
from fastapi.responses import Response

from app.api.deps import ServiceDep

router = APIRouter(prefix="/export", tags=["export"])


@router.get(
    "/links",
    response_class=Response,
    summary="Экспорт всех ссылок в CSV-файл",
)
async def export_links_csv(service: ServiceDep) -> Response:
    """Отдаёт все ссылки сервиса одним CSV-файлом (attachment)."""
    content = await service.export_links_csv()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="links_export.csv"'},
    )
