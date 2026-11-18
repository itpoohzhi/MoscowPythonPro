"""Чистые валидаторы входных данных (SSRF-защита целевых URL).

Живут в слое `schemas`, чтобы схемы не импортировали `app.core`; `app/core/security.py`
переэкспортирует их для остального кода.
"""

import ipaddress
import re
import socket
from urllib.parse import urlparse

import structlog

logger = structlog.get_logger()

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]
CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")
NUMERIC_IPV4_LABEL = re.compile(r"^(0[xX][0-9a-fA-F]+|[0-9]+)$")


class SecuritySSRFError(ValueError):
    """Исключение при попытке обращения к приватным IP или локальным адресам."""

    pass


def validate_target_url_security(url_str: str) -> str:
    """
    Валидирует URL без блокирующего DNS-запроса:
    1. Проверяет допустимые протоколы (только http и https).
    2. Блокирует localhost и имена внутренних сервисов.
    3. Если хост является IP-адресом, проверяет его на принадлежность к приватным диапазонам.

    `linksvc` только возвращает HTTP 307 через `RedirectResponse` и никогда не выполняет
    серверный HTTP-запрос к `target_url`.
    """
    parsed = urlparse(url_str.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise SecuritySSRFError(
            f"Запрещенный протокол: {parsed.scheme}. Разрешены только HTTP и HTTPS."
        )

    if parsed.username or parsed.password:
        raise ValueError("Учётные данные в URL запрещены политикам безопасности (SSRF)")

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        raise SecuritySSRFError("В URL отсутствует корректный хост.")

    if hostname in (
        "localhost",
        "linkdb",
        "redis",
        "postgres",
        "testserver",
        "db",
    ) or hostname.endswith((".local", ".internal")):
        raise SecuritySSRFError(f"Запрещен внутренний хост: {hostname}")

    # Проверка строковых IP-адресов без DNS-разрешения доменных имён.
    ip_literal = hostname.strip("[]")
    try:
        ip_obj = ipaddress.ip_address(ip_literal)
    except ValueError:
        if all(NUMERIC_IPV4_LABEL.fullmatch(label) for label in ip_literal.split(".")):
            raise SecuritySSRFError(
                "Нестандартные числовые/octal/hex формы IP-адресов запрещены "
                "политикой безопасности (SSRF)"
            ) from None
        try:
            ip_obj = ipaddress.IPv4Address(socket.inet_aton(ip_literal))
        except OSError:
            # Доменное имя (например moscowpython.ru) не является прямым IP.
            ip_obj = None

    if ip_obj is not None:
        checked_ip = (
            ip_obj.ipv4_mapped
            if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped is not None
            else ip_obj
        )
        if (
            checked_ip.is_private
            or checked_ip.is_loopback
            or checked_ip.is_link_local
            or checked_ip.is_reserved
            or checked_ip.is_multicast
            or checked_ip.is_unspecified
            or (isinstance(checked_ip, ipaddress.IPv4Address) and checked_ip in CGNAT_NETWORK)
        ):
            raise SecuritySSRFError(f"Запрещен приватный IP-адрес: {hostname}")
        for net in BLOCKED_NETWORKS:
            if checked_ip.version == net.version and checked_ip in net:
                raise SecuritySSRFError(f"IP-адрес {hostname} входит в заблокированную сеть {net}")

    return url_str
