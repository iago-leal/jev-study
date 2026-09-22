"""Requisições HTTP com timeout, cortesia por domínio e alternativa do Internet Archive."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable

from .config import HTTP_TIMEOUT_S, SAME_HOST_DELAY_S, USER_AGENT


class FetchError(Exception):
    """Falha de coleta com motivo legível para o relatório."""


@dataclass
class Response:
    url: str
    status: int
    content_type: str
    body: str


Fetcher = Callable[[str], Response]

_last_hit: dict[str, float] = {}


def http_get(url: str, timeout: float = HTTP_TIMEOUT_S) -> Response:
    """GET real. Levanta FetchError com o código HTTP ou 'timeout'."""
    host = urllib.parse.urlsplit(url).netloc
    wait = SAME_HOST_DELAY_S - (time.monotonic() - _last_hit.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/markdown,text/plain,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return Response(resp.geturl(), resp.status, resp.headers.get("Content-Type", ""), raw.decode(charset, "replace"))
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code}") from None
    except (TimeoutError, urllib.error.URLError) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, TimeoutError) or "timed out" in str(reason):
            raise FetchError("timeout") from None
        raise FetchError(f"erro de rede: {reason}") from None
    finally:
        _last_hit[host] = time.monotonic()


def wayback_snapshot_url(url: str, fetch: Fetcher) -> str | None:
    """Consulta a API de disponibilidade e devolve a URL bruta (`id_`) do snapshot mais próximo."""
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    try:
        data = json.loads(fetch(api).body)
    except (FetchError, json.JSONDecodeError):
        return None
    closest = (data.get("archived_snapshots") or {}).get("closest") or {}
    if not closest.get("available") or not closest.get("timestamp"):
        return None
    return f"https://web.archive.org/web/{closest['timestamp']}id_/{url}"
