from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import socket
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


DEFAULT_MAX_BYTES = 5 * 1024 * 1024


def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported URL scheme: {parsed.scheme or '<missing>'}")
    if not parsed.hostname:
        raise ValueError("URL has no hostname")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("refusing localhost URL")

    try:
        resolved = socket.getaddrinfo(hostname, parsed.port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"cannot resolve hostname: {hostname}") from exc

    if not resolved:
        raise ValueError(f"cannot resolve hostname: {hostname}")
    for _family, _type, _proto, _canonname, sockaddr in resolved:
        ip = ipaddress.ip_address(sockaddr[0])
        if not ip.is_global:
            raise ValueError(f"refusing non-public address for {hostname}: {ip}")
    return url


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass
class _LimitedResponse:
    response: object
    max_bytes: int

    @property
    def headers(self):
        return self.response.headers

    def geturl(self):
        return self.response.geturl()

    def read(self, amt: int | None = None):
        if amt is not None:
            return self.response.read(min(amt, self.max_bytes + 1))
        payload = self.response.read(self.max_bytes + 1)
        if len(payload) > self.max_bytes:
            raise ValueError(f"response exceeds {self.max_bytes} byte limit")
        return payload

    def close(self):
        return self.response.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


def safe_urlopen(request_or_url, timeout: int = 10, max_bytes: int = DEFAULT_MAX_BYTES):
    if isinstance(request_or_url, Request):
        url = request_or_url.full_url
    else:
        url = str(request_or_url)
    validate_public_url(url)
    opener = build_opener(_SafeRedirectHandler())
    response = opener.open(request_or_url, timeout=timeout)
    final_url = response.geturl()
    try:
        validate_public_url(final_url)
    except Exception:
        response.close()
        raise
    return _LimitedResponse(response=response, max_bytes=max_bytes)
