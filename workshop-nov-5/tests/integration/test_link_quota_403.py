"""Интеграционные тесты квоты активных ссылок плана FREE на HTTP-слое (волна 4)."""

from __future__ import annotations

import asyncio
import tempfile
from collections.abc import AsyncGenerator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.billing import _repo_instance
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.schemas.billing import PlanType, WalletBalance


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with tempfile.TemporaryDirectory(prefix="linksvc-tests-") as tmp:
        engine = create_async_engine(f"sqlite+aiosqlite:///{Path(tmp) / 'test_links.db'}")

        async def create_schema() -> None:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(create_schema())
        factory = async_sessionmaker(engine, expire_on_commit=False)

        async def override_get_db() -> AsyncGenerator[AsyncSession]:
            async with factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db] = override_get_db
        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.pop(get_db, None)
            asyncio.run(engine.dispose())


@pytest.fixture(autouse=True)
def clean_quota_users():
    """Изолировать состояние квоты тестовых пользователей между тестами."""
    for uid in (7100, 7200, 7300, 7400, 7500, 7600):
        _repo_instance.wallets.pop(uid, None)
        _repo_instance.active_links.pop(uid, None)
    yield


def _create_link(client: TestClient, user_id: int | None = None, url: str | None = None):
    headers = {"X-User-Id": str(user_id)} if user_id is not None else None
    return client.post(
        "/links",
        json={"target_url": url or "https://example.com/page"},
        headers=headers,
    )


def test_anonymous_link_creation_not_quota_limited(client):
    """Анонимная ссылка (без user_id): квота не проверяется, anon path сохранён."""
    response = _create_link(client)
    assert response.status_code == 201
    assert response.json()["disabled"] is False


def test_free_plan_user_hits_403_on_eleventh_link(client):
    """11-я активная ссылка владельца FREE -> HTTP 403 с QuotaExceededResponse."""
    uid = 7100
    top_up = client.post("/billing/wallets/top-up", json={"user_id": uid, "amount": 100})
    assert top_up.status_code == 200

    for i in range(10):
        response = _create_link(client, user_id=uid, url=f"https://example.com/free{i}")
        assert response.status_code == 201, f"link #{i + 1}: {response.status_code}"

    exceeded = _create_link(client, user_id=uid, url="https://example.com/eleventh")
    assert exceeded.status_code == 403
    body = exceeded.json()["detail"]
    assert body["detail"] == "Free plan link quota exceeded"
    assert body["plan"] == "free"
    assert body["limit"] == 10
    assert body["active_links"] == 10


def test_pro_plan_user_is_not_limited(client):
    """PRO-план не лимитируется: больше 10 активных ссылок проходят со 201."""
    uid = 7200
    # Учебный контур: план задаётся фикстурой прямо в InMemory-репозитории
    # (API top-up всегда создаёт FREE-кошелёк).
    _repo_instance.wallets[uid] = WalletBalance(user_id=uid, balance=0, plan=PlanType.PRO)

    for i in range(12):
        response = _create_link(client, user_id=uid, url=f"https://example.com/pro{i}")
        assert response.status_code == 201, f"link #{i + 1}: {response.status_code}"


def test_disable_releases_quota_slot(client):
    """Disable снимает ссылку с учёта: следующий create снова проходит (201)."""
    uid = 7300
    top_up = client.post("/billing/wallets/top-up", json={"user_id": uid, "amount": 100})
    assert top_up.status_code == 200

    for i in range(10):
        response = _create_link(client, user_id=uid, url=f"https://example.com/rel{i}")
        assert response.status_code == 201

    assert _create_link(client, user_id=uid).status_code == 403

    # Disable одной активной ссылки
    code = client.get("/links").json()[0]["short_code"]
    disabled = client.post(f"/links/{code}/disable", headers={"X-User-Id": str(uid)})
    assert disabled.status_code == 200
    assert disabled.json()["disabled"] is True

    recreated = _create_link(client, user_id=uid, url="https://example.com/after-disable")
    assert recreated.status_code == 201


def test_v1_disable_with_user_header_releases_quota_once(client: TestClient) -> None:
    uid = 7400
    client.post("/billing/wallets/top-up", json={"user_id": uid, "amount": 100})
    created = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/v1-disable", "custom_code": "quota-v1-off"},
        headers={"X-User-Id": str(uid)},
    )
    assert created.status_code == 201
    assert _repo_instance.active_links[uid] == 1

    first = client.post("/api/v1/links/quota-v1-off/disable", headers={"X-User-Id": str(uid)})
    second = client.post("/api/v1/links/quota-v1-off/disable", headers={"X-User-Id": str(uid)})
    assert first.status_code == second.status_code == 200
    assert _repo_instance.active_links[uid] == 0


def test_v1_enable_enforces_quota(client: TestClient) -> None:
    uid = 7500
    client.post("/billing/wallets/top-up", json={"user_id": uid, "amount": 100})
    parked = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/parked", "custom_code": "quota-parked"},
        headers={"X-User-Id": str(uid)},
    )
    assert parked.status_code == 201
    assert (
        client.post(
            "/api/v1/links/quota-parked/disable", headers={"X-User-Id": str(uid)}
        ).status_code
        == 200
    )
    for index in range(10):
        response = client.post(
            "/api/v1/links",
            json={
                "original_url": f"https://example.com/full-{index}",
                "custom_code": f"quota-full-{index}",
            },
            headers={"X-User-Id": str(uid)},
        )
        assert response.status_code == 201

    enabled = client.post("/api/v1/links/quota-parked/enable", headers={"X-User-Id": str(uid)})
    assert enabled.status_code == 403
    assert _repo_instance.active_links[uid] == 10


def test_v1_conflict_does_not_leak_quota(client: TestClient) -> None:
    uid = 7600
    client.post("/billing/wallets/top-up", json={"user_id": uid, "amount": 100})
    payload = {"original_url": "https://example.com/conflict", "custom_code": "quota-conflict"}
    headers = {"X-User-Id": str(uid)}
    assert client.post("/api/v1/links", json=payload, headers=headers).status_code == 201
    assert client.post("/api/v1/links", json=payload, headers=headers).status_code == 409
    assert _repo_instance.active_links[uid] == 1
