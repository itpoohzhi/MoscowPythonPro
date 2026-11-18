"""Интеграционные тесты про-экспорта ссылок (GET /api/v1/export/links/pro)."""

import asyncio

from httpx import AsyncClient

PRO_EXPORT_URL = "/api/v1/export/links/pro"


async def _create_link(client: AsyncClient, url: str, **extra: object) -> str:
    response = await client.post("/api/v1/links", json={"original_url": url, **extra})
    assert response.status_code == 201, response.text
    return str(response.json()["short_code"])


async def test_export_pro_empty_db(client: AsyncClient) -> None:
    """На пустой базе отдаётся пустая страница с нулевым total."""
    response = await client.get(PRO_EXPORT_URL)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_export_pro_lists_created_links(client: AsyncClient) -> None:
    """Созданные ссылки попадают в выгрузку в порядке «новые первыми»."""
    first = await _create_link(client, "https://example.com/pro/1")
    second = await _create_link(client, "https://example.com/pro/2")

    response = await client.get(PRO_EXPORT_URL)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    codes = [item["short_code"] for item in body["items"]]
    assert codes == [second, first]  # новые первыми
    item = body["items"][0]
    assert item["target_url"] == "https://example.com/pro/2"
    assert item["status"] == "active"
    assert item["clicks"] == 0


async def test_export_pro_status_filter_disabled(client: AsyncClient) -> None:
    """Фильтр `status=disabled` оставляет только выключенные ссылки."""
    active_code = await _create_link(client, "https://example.com/pro/keep")
    disabled_code = await _create_link(client, "https://example.com/pro/off")
    disable_response = await client.post(f"/api/v1/links/{disabled_code}/disable")
    assert disable_response.status_code == 200

    response = await client.get(PRO_EXPORT_URL, params={"status": "disabled"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["short_code"] for item in body["items"]] == [disabled_code]
    assert body["items"][0]["status"] == "disabled"

    active_response = await client.get(PRO_EXPORT_URL, params={"status": "active"})
    assert active_response.status_code == 200
    assert [item["short_code"] for item in active_response.json()["items"]] == [active_code]


async def test_export_pro_status_filter_expired(client: AsyncClient) -> None:
    """Фильтр `status=expired` отдаёт только просроченные ссылки (TTL=1s)."""
    living_code = await _create_link(client, "https://example.com/pro/living")
    await _create_link(client, "https://example.com/pro/dying", ttl_seconds=1)
    await asyncio.sleep(1.2)

    response = await client.get(PRO_EXPORT_URL, params={"status": "expired"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "expired"

    active_response = await client.get(PRO_EXPORT_URL, params={"status": "active"})
    assert active_response.json()["items"][0]["short_code"] == living_code


async def test_export_pro_search_filter(client: AsyncClient) -> None:
    """Поиск по подстроке URL фильтрует выгрузку без учёта регистра."""
    await _create_link(client, "https://example.com/pro/alpha")
    await _create_link(client, "https://example.com/other/beta")

    response = await client.get(PRO_EXPORT_URL, params={"search": "ALPHA"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["target_url"] == "https://example.com/pro/alpha"


async def test_export_pro_pagination(client: AsyncClient) -> None:
    """Пагинация ограничивает страницу и показывает полное `total`."""
    for i in range(3):
        await _create_link(client, f"https://example.com/pro/page/{i}")

    response = await client.get(PRO_EXPORT_URL, params={"limit": 2, "offset": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 1


async def test_export_pro_validates_pagination_bounds(client: AsyncClient) -> None:
    """Небезопасные границы пагинации отклоняются статусом 422."""
    limit_zero = await client.get(PRO_EXPORT_URL, params={"limit": 0})
    assert limit_zero.status_code == 422

    limit_too_big = await client.get(PRO_EXPORT_URL, params={"limit": 1001})
    assert limit_too_big.status_code == 422

    offset_negative = await client.get(PRO_EXPORT_URL, params={"offset": -1})
    assert offset_negative.status_code == 422


async def test_export_pro_validates_search_length_and_status(client: AsyncClient) -> None:
    """Слишком длинный поиск и неизвестный статус отклоняются статусом 422."""
    long_search = await client.get(PRO_EXPORT_URL, params={"search": "x" * 101})
    assert long_search.status_code == 422

    unknown_status = await client.get(PRO_EXPORT_URL, params={"status": "archived"})
    assert unknown_status.status_code == 422
