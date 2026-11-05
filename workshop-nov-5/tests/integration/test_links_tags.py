"""Интеграционные тесты фильтрации ссылок по тегам (LINK-43).

Контракт: specs/LINK-43-tag-filter-ears.md
"""

from httpx import AsyncClient

LIST_URL = "/api/v1/links"


async def _create_link(client: AsyncClient, url: str, **extra: object) -> dict:
    response = await client.post(LIST_URL, json={"original_url": url, **extra})
    assert response.status_code == 201, response.text
    return dict(response.json())


async def test_create_link_with_tags_echoes_tags(client: AsyncClient) -> None:
    """REQ-001/REQ-002: созданная ссылка хранит и возвращает свои теги."""
    body = await _create_link(client, "https://example.com/tagged", tags=["docs", "promo"])
    assert body["tags"] == ["docs", "promo"]


async def test_underscore_tag_matches_nothing_else(client: AsyncClient) -> None:
    """RW-001: '_' в теге — не LIKE-wildcard: только точное совпадение."""
    hyphen = await _create_link(client, "https://example.com/hyphen", tags=["a-b"])
    anychar = await _create_link(client, "https://example.com/axb", tags=["axb"])
    exact = await _create_link(client, "https://example.com/underscore", tags=["a_b"])

    response = await client.get(LIST_URL, params={"tag": "a_b"})
    assert response.status_code == 200
    returned = response.json()
    assert [item["short_code"] for item in returned] == [exact["short_code"]]
    assert returned[0]["tags"] == ["a_b"]
    # Непов付け: кейс из acceptance брифа — 'mydocs' не ловится поиском 'docs' (RW-001).
    stem = await _create_link(client, "https://example.com/mydocs", tags=["mydocs"])
    docs = await _create_link(client, "https://example.com/docs", tags=["docs"])
    res_docs = await client.get(LIST_URL, params={"tag": "docs"})
    assert [item["short_code"] for item in res_docs.json()] == [docs["short_code"]]
    res_mydocs = await client.get(LIST_URL, params={"tag": "mydocs"})
    assert [item["short_code"] for item in res_mydocs.json()] == [stem["short_code"]]
    _ = hyphen
    _ = anychar


async def test_create_link_without_tags_defaults_empty(client: AsyncClient) -> None:
    """REQ-003/REQ-008: без тегов и с пустым массивом — контракт со старыми ключами."""
    missing = await _create_link(client, "https://example.com/no-tags")
    assert missing["tags"] == []
    assert missing["short_code"]
    assert missing["status"] == "active"

    explicit = await _create_link(client, "https://example.com/empty-tags", tags=[])
    assert explicit["tags"] == []


async def test_list_filter_by_single_tag(client: AsyncClient) -> None:
    """REQ-004: ?tag=docs отдаёт только ссылки с этим тегом, новые первыми."""
    _ = await _create_link(client, "https://example.com/other", tags=["misc"])
    first_match = await _create_link(client, "https://example.com/docs-one", tags=["docs"])
    second_match = await _create_link(
        client, "https://example.com/docs-two", tags=["docs", "promo"]
    )

    response = await client.get(LIST_URL, params={"tag": "docs"})
    assert response.status_code == 200
    codes = [item["short_code"] for item in response.json()]
    assert codes == [second_match["short_code"], first_match["short_code"]]
    for item in response.json():
        assert "docs" in item["tags"]


async def test_list_untagged_links_not_returned_by_tag_filter(client: AsyncClient) -> None:
    """FU-005/REQ-009: ссылка с пустым массивом tags исключается из выборки ?tag=."""
    tagged = await _create_link(client, "https://example.com/tagged-x", tags=["docs"])
    await _create_link(client, "https://example.com/empty-tags-x", tags=[])

    response = await client.get(LIST_URL, params={"tag": "docs"})
    assert response.status_code == 200
    assert [item["short_code"] for item in response.json()] == [tagged["short_code"]]


LEGACY_CREATE_RESPONSE_KEYS = {
    "id",
    "short_code",
    "original_url",
    "target_url",
    "short_url",
    "clicks_count",
    "clicks",
    "is_active",
    "disabled",
    "status",
    "created_at",
    "expires_at",
}


async def test_create_response_keys_unchanged(client: AsyncClient) -> None:
    """RW-002: старый контракт ответа POST /api/v1/links — только новое поле tags."""
    body = await _create_link(client, "https://example.com/compat")
    added = set(body) - LEGACY_CREATE_RESPONSE_KEYS
    assert added == {"tags"}
    # Двусторонняя проверка (RW-002/round2 N3): ни один старый ключ не удалён и не переименован.
    assert LEGACY_CREATE_RESPONSE_KEYS <= set(body)


async def test_list_filter_by_unknown_tag_returns_empty(client: AsyncClient) -> None:
    """REQ-005: несуществующий тег — 200 и пустой список."""
    await _create_link(client, "https://example.com/lonely", tags=["misc"])

    response = await client.get(LIST_URL, params={"tag": "nothing"})
    assert response.status_code == 200
    assert response.json() == []


async def test_list_without_tag_keeps_old_contract(client: AsyncClient) -> None:
    """Обратная совместимость: без ?tag= отдаётся полный список с тегами в ответе."""
    await _create_link(client, "https://example.com/a", tags=["alpha"])
    await _create_link(client, "https://example.com/b")

    response = await client.get(LIST_URL)
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all("tags" in item for item in response.json())


async def test_invalid_tag_rejected_with_422(client: AsyncClient) -> None:
    """REQ-006: тег вне паттерна отклоняется со статусом 422."""
    for bad_tag in ("Uppercase", "a", "x" * 33, "bad tag", "<tag>", ""):
        response = await client.get(LIST_URL, params={"tag": bad_tag})
        assert response.status_code == 422, f"tag={bad_tag!r} -> {response.status_code}"

    create_response = await client.post(
        LIST_URL, json={"original_url": "https://example.com/bad", "tags": ["Bad!"]}
    )
    assert create_response.status_code == 422


async def test_too_many_tags_rejected_with_422(client: AsyncClient) -> None:
    """REQ-007: более 10 тегов отклоняется со статусом 422."""
    response = await client.post(
        LIST_URL,
        json={
            "original_url": "https://example.com/many",
            "tags": [f"tag{i:02d}" for i in range(11)],
        },
    )
    assert response.status_code == 422
