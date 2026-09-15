"""Pinning tests for SSRF-protected DNS resolution."""

import asyncio
import socket

import httpx
import pytest

from web_similarity_audit.fetcher import SSRFProtectedTransport


@pytest.mark.asyncio
async def test_transport_pins_vetted_address_but_keeps_host_and_sni(monkeypatch):
    loop = asyncio.get_running_loop()

    async def public_answer(host, port, **kwargs):
        assert host == "a.example"
        return [(2, 1, 6, "", ("93.184.216.34", port))]

    captured = {}

    async def capture_base_transport(self, request):
        captured["url_host"] = request.url.host
        captured["host_header"] = request.headers["host"]
        captured["sni"] = request.extensions["sni_hostname"]
        return httpx.Response(200, request=request, text="ok")

    monkeypatch.setattr(loop, "getaddrinfo", public_answer)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", capture_base_transport)
    response = await SSRFProtectedTransport().handle_async_request(
        httpx.Request("GET", "https://a.example:8443/path")
    )

    assert response.status_code == 200
    assert captured == {
        "url_host": "93.184.216.34",
        "host_header": "a.example:8443",
        "sni": "a.example",
    }


@pytest.mark.asyncio
async def test_transport_pins_ipv6_literal_with_brackets(monkeypatch):
    loop = asyncio.get_running_loop()
    ipv6 = "2606:2800:220:1:248:1893:25c8:1946"

    async def public_answer(host, port, **kwargs):
        assert host == "v6.example"
        return [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", (ipv6, port, 0, 0))]

    captured = {}

    async def capture_base_transport(self, request):
        captured["url"] = str(request.url)
        captured["url_host"] = request.url.host
        captured["host_header"] = request.headers["host"]
        captured["sni"] = request.extensions["sni_hostname"]
        return httpx.Response(200, request=request, text="ok")

    monkeypatch.setattr(loop, "getaddrinfo", public_answer)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", capture_base_transport)
    response = await SSRFProtectedTransport().handle_async_request(
        httpx.Request("GET", "https://v6.example/path")
    )

    assert response.status_code == 200
    assert captured == {
        "url": f"https://[{ipv6}]/path",
        "url_host": ipv6,
        "host_header": "v6.example",
        "sni": "v6.example",
    }
