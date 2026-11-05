import csv
import io

from httpx import AsyncClient


async def test_export_links_csv_with_rows(client: AsyncClient) -> None:
    """Созданные ссылки полностью выгружаются в CSV-файл (attachment)."""
    codes = []
    for i in range(3):
        res = await client.post(
            "/api/v1/links", json={"original_url": f"https://example.com/export/{i}"}
        )
        assert res.status_code == 201
        codes.append(res.json()["short_code"])

    res = await client.get("/api/v1/export/links")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert res.headers["content-disposition"] == 'attachment; filename="links_export.csv"'

    rows = list(csv.DictReader(io.StringIO(res.text)))
    assert len(rows) == 3
    assert {row["short_code"] for row in rows} == set(codes)
    for row in rows:
        assert row["target_url"].startswith("https://example.com/export/")
        assert row["clicks"] == "0"
        assert row["disabled"] == "false"
        assert row["expires_at"] == ""


async def test_export_links_csv_empty_db(client: AsyncClient) -> None:
    """На пустой базе отдаётся валидный CSV только с заголовком."""
    res = await client.get("/api/v1/export/links")
    assert res.status_code == 200
    rows = list(csv.DictReader(io.StringIO(res.text)))
    assert rows == []


async def test_export_links_csv_reflects_disabled_state(client: AsyncClient) -> None:
    """Выключенная ссылка выгружается с флагом `disabled=true`."""
    res = await client.post("/api/v1/links", json={"original_url": "https://example.com/off"})
    assert res.status_code == 201
    code = res.json()["short_code"]

    disable_res = await client.post(f"/api/v1/links/{code}/disable")
    assert disable_res.status_code == 200

    export_res = await client.get("/api/v1/export/links")
    assert export_res.status_code == 200
    rows = list(csv.DictReader(io.StringIO(export_res.text)))
    assert len(rows) == 1
    assert rows[0]["short_code"] == code
    assert rows[0]["disabled"] == "true"
