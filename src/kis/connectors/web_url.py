"""Single-URL web clip connector (KIS-008).

Lightweight, explicit "URL -> traceable knowledge card". NOT a heavy crawler —
Crawl4AI is a later optional adapter (KIS-009). This baseline is pure stdlib.

Pipeline:
    validate_url (SSRF defense) -> fetch_url -> extract_web_page
        -> classify -> web_page_to_card -> SQLite -> Obsidian

Three hard rules (per spec): SSRF defense first, blocked URLs never stored,
all logic except fetch_url is network-free and unit-tested with a mock fetcher.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from ..card import content_hash, infer_projects, new_card, normalize_url, now_iso, url_hash  # noqa: F401
from ..classify import classify_bookmark

_UA = "Mozilla/5.0 (compatible; KIS-WebClip/0.2; +https://kis.local)"
_ALLOWED_SCHEMES = {"http", "https"}
_BLOCKED_HOSTNAMES = {"localhost", "ip6-localhost", "ip6-loopback", "0.0.0.0", "metadata.google.internal"}
_PREVIEW_CHARS = 4000


class UrlSafetyError(ValueError):
    """Raised when a URL fails the SSRF / scheme safety checks."""


# --- SSRF defense (P0) -------------------------------------------------------

def _maybe_ip(host: str) -> ipaddress._BaseAddress | None:
    h = host.strip("[]")  # IPv6 literals arrive bracketed
    try:
        return ipaddress.ip_address(h)
    except ValueError:
        return None


def _is_public_ip(ip: ipaddress._BaseAddress) -> bool:
    return not (
        ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
        or ip.is_unspecified or ip.is_multicast
    )


def validate_url(url: str) -> str:
    """Pure (no DNS) scheme/host safety check. Returns normalized_url or raises.

    Blocks non-http(s) schemes (file/ftp/chrome/about/javascript/data/...),
    localhost-family hostnames, and IP *literals* in private/loopback/link-local/
    reserved ranges (incl. the 169.254.169.254 cloud metadata address). Hostname
    -> internal-IP resolution is additionally enforced in fetch_url.
    """
    parts = urlsplit((url or "").strip())
    scheme = parts.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise UrlSafetyError(f"blocked scheme: {scheme or '(none)'}")
    host = parts.hostname
    if not host:
        raise UrlSafetyError("missing host")
    h = host.lower()
    if h in _BLOCKED_HOSTNAMES or h.endswith(".localhost"):
        raise UrlSafetyError(f"blocked host: {host}")
    ip = _maybe_ip(host)
    if ip is not None and not _is_public_ip(ip):
        raise UrlSafetyError(f"blocked non-public ip: {host}")
    return normalize_url(url)


def _assert_resolves_public(host: str) -> None:
    """Network step: resolve host and reject if any A/AAAA is non-public."""
    import socket
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise UrlSafetyError(f"cannot resolve host: {host} ({e})")
    for info in infos:
        ip = _maybe_ip(info[4][0])
        if ip is not None and not _is_public_ip(ip):
            raise UrlSafetyError(f"host {host} resolves to non-public ip {ip}")


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)  # re-check each hop -> closes redirect-SSRF
        _assert_resolves_public(urlsplit(newurl).hostname or "")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# --- fetch (the only network code; mocked in tests) --------------------------

@dataclass
class WebPageRaw:
    url: str
    final_url: str
    status: int
    content_type: str
    html: str
    error: str | None = None


def fetch_url(url: str, timeout: int = 10, max_bytes: int = 2_000_000) -> WebPageRaw:
    validate_url(url)
    _assert_resolves_public(urlsplit(url).hostname or "")
    req = Request(url, headers={"User-Agent": _UA, "Accept": "text/html,application/xhtml+xml"})
    opener = build_opener(_SafeRedirectHandler())
    try:
        with opener.open(req, timeout=timeout) as resp:
            status = getattr(resp, "status", resp.getcode()) or 0
            ctype = resp.headers.get("Content-Type", "")
            raw = resp.read(max_bytes)
            final_url = resp.geturl()
        charset = "utf-8"
        m = re.search(r"charset=([\w-]+)", ctype, re.I)
        if m:
            charset = m.group(1)
        html = raw.decode(charset, errors="replace") if "html" in ctype.lower() or not ctype else raw.decode("utf-8", "replace")
        return WebPageRaw(url=url, final_url=final_url, status=status, content_type=ctype, html=html, error=None)
    except Exception as e:  # network/HTTP errors are data, not crashes
        return WebPageRaw(url=url, final_url=url, status=0, content_type="", html="", error=str(e))


# --- extraction (pure) -------------------------------------------------------

@dataclass
class WebPageExtract:
    url: str
    normalized_url: str
    title: str
    description: str
    site_name: str
    lang: str
    text_preview: str
    http_status: int
    fetched_at: str
    fetch_error: str | None = None


class _PageParser(HTMLParser):
    _SKIP = {"script", "style", "noscript", "template", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0
        self.lang = ""
        self.meta: dict[str, str] = {}
        self.text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        d = dict(attrs)
        if tag == "html" and d.get("lang"):
            self.lang = d["lang"]
        elif tag == "title":
            self._in_title = True
        elif tag in self._SKIP:
            self._skip_depth += 1
        elif tag == "meta":
            key = (d.get("property") or d.get("name") or "").lower()
            content = d.get("content")
            if key and content:
                self.meta.setdefault(key, content)

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == "meta":
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        elif tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        elif self._skip_depth == 0:
            s = data.strip()
            if s:
                self.text_parts.append(s)


def extract_web_page(raw: WebPageRaw) -> WebPageExtract:
    p = _PageParser()
    if raw.html:
        p.feed(raw.html)
    title = (p.meta.get("og:title") or "".join(p.title_parts).strip() or raw.url)
    description = p.meta.get("description") or p.meta.get("og:description") or ""
    site_name = p.meta.get("og:site_name") or urlsplit(raw.url).hostname or ""
    text = re.sub(r"\s+", " ", " ".join(p.text_parts)).strip()
    return WebPageExtract(
        url=raw.url,
        normalized_url=normalize_url(raw.url),
        title=title.strip(),
        description=description.strip(),
        site_name=site_name.strip(),
        lang=(p.lang or "unknown").strip(),
        text_preview=text[:_PREVIEW_CHARS],
        http_status=raw.status,
        fetched_at=now_iso(),
        fetch_error=raw.error,
    )


def web_page_to_card(page: WebPageExtract, cls: dict[str, str] | None = None,
                     import_batch_id: str | None = None) -> dict[str, Any]:
    cls = cls or classify_bookmark(page.title, page.url, page.site_name)
    body = (
        f"## Source\n- URL: {page.url}\n- Site: {page.site_name}\n"
        f"- Fetched at: {page.fetched_at}\n- HTTP status: {page.http_status}\n\n"
        f"## Description\n{page.description or '(none)'}\n\n"
        f"## Text Preview\n{page.text_preview or '(empty)'}\n\n"
        f"## Initial Classification\n- Category: {cls['category']}\n- Sensitivity: {cls['sensitivity']}\n\n"
        f"## Next Action\n- [ ] review\n- [ ] summarize\n- [ ] decide whether to promote to canonical"
    )
    return new_card(
        source_type="web_clip",
        url=page.url,
        title=page.title,
        body_md=body,
        content_hash_value=content_hash(page.normalized_url, page.title, page.description, page.text_preview),
        lang=page.lang,
        category=cls["category"],
        sensitivity=cls["sensitivity"],
        description=page.description,
        text_preview=page.text_preview,
        site_name=page.site_name,
        http_status=page.http_status,
        fetched_at=page.fetched_at,
        fetch_error=page.fetch_error,
        import_batch_id=import_batch_id,
        projects=infer_projects(f"{page.title} {page.normalized_url} {page.description}"),
    )
