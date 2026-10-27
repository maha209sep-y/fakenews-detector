"""
Fetch the readable text of a news article from a URL.

Includes SSRF protection: only http/https, and the hostname must not resolve to a
private / loopback / link-local address.
"""
import ipaddress
import re
import socket
from html import unescape
from urllib.parse import urlparse

import httpx

MAX_BYTES = 2_000_000


class FetchError(Exception):
    pass


def _check_public_host(hostname: str):
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise FetchError("Could not resolve that website.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise FetchError("That address is not allowed.")


def _html_to_text(html: str) -> tuple[str, str]:
    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    title = unescape(title_m.group(1)).strip() if title_m else ""
    html = re.sub(r"(?is)<(script|style|noscript|header|footer|nav|aside|form)[^>]*>.*?</\1>", " ", html)
    paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", html)
    body = " ".join(re.sub(r"(?s)<[^>]+>", " ", p) for p in paras)
    if len(body) < 200:  # fall back to all text
        body = re.sub(r"(?s)<[^>]+>", " ", html)
    body = unescape(re.sub(r"\s+", " ", body)).strip()
    return title, body


def fetch_article(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError("Invalid URL.")
    _check_public_host(parsed.hostname)

    try:
        with httpx.Client(follow_redirects=False, timeout=10.0,
                          headers={"User-Agent": "FakeNewsDetectorBot/1.0"}) as client:
            # follow up to 3 redirects manually, re-checking the host each time
            for _ in range(4):
                r = client.get(url)
                if r.is_redirect:
                    url = str(r.next_request.url) if r.next_request else r.headers.get("location", "")
                    p = urlparse(url)
                    if not p.hostname or p.scheme not in ("http", "https"):
                        raise FetchError("Bad redirect.")
                    _check_public_host(p.hostname)
                    continue
                break
            else:
                raise FetchError("Too many redirects.")
    except httpx.HTTPError as e:
        raise FetchError(f"Could not download the page ({type(e).__name__}).")

    if r.status_code >= 400:
        raise FetchError(f"The website returned status {r.status_code}.")
    if len(r.content) > MAX_BYTES:
        raise FetchError("Page too large.")

    title, body = _html_to_text(r.text)
    text = f"{title}. {body}".strip(". ")
    if len(text) < 40:
        raise FetchError("Could not find readable article text on that page.")
    return text[:20000]