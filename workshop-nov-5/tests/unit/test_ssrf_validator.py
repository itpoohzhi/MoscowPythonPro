"""Регрессии SSRF-валидации целевых URL."""

import pytest

from app.schemas.validators import SecuritySSRFError, validate_target_url_security


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost./admin",
        "http://db:5432/",
        "http://224.0.0.1/",
        "http://240.0.0.1/",
        "http://0.0.0.0/",
        "http://2130706433/admin",
        "http://0x7f000001/admin",
        "http://0177.0.0.1/admin",
        "http://127.1/admin",
        "http://100.64.0.1/admin",
        "http://[::ffff:127.0.0.1]/admin",
    ],
)
def test_rejects_internal_or_non_public_targets(url: str) -> None:
    with pytest.raises(SecuritySSRFError):
        validate_target_url_security(url)


def test_rejects_credentials_in_url() -> None:
    with pytest.raises(
        ValueError,
        match="Учётные данные в URL запрещены политикам безопасности \\(SSRF\\)",
    ):
        validate_target_url_security("http://user:pass@example.com/")
