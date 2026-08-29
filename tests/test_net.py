import socket

import pytest

from xfetch.net import validate_public_url


def test_validate_public_url_blocks_loopback(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))])
    with pytest.raises(ValueError, match="non-public"):
        validate_public_url("https://example.test/private")


def test_validate_public_url_blocks_link_local_metadata(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80))])
    with pytest.raises(ValueError, match="non-public"):
        validate_public_url("http://metadata.invalid/latest")


def test_validate_public_url_accepts_public_address(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))])
    assert validate_public_url("https://example.com/article") == "https://example.com/article"
