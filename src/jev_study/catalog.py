"""Leitura e validação do catálogo `sources.toml` (source-collection RF-01)."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .config import KINDS, TIER_WEIGHTS

_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REQUIRED = ("id", "title", "url", "kind", "tier")


class CatalogError(Exception):
    """Catálogo inválido: nada deve ser coletado."""


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    url: str
    kind: str
    tier: str
    notes: str = ""


def load_catalog(path: Path) -> list[Source]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CatalogError(f"catálogo não encontrado: {path}") from None
    except tomllib.TOMLDecodeError as exc:
        raise CatalogError(f"TOML malformado em {path}: {exc}") from None
    return parse_catalog(data.get("source", []))


def parse_catalog(entries: list[dict]) -> list[Source]:
    sources: list[Source] = []
    seen: set[str] = set()
    for n, entry in enumerate(entries, start=1):
        where = f"entrada {n}"
        missing = [k for k in _REQUIRED if not str(entry.get(k, "")).strip()]
        if missing:
            raise CatalogError(f"{where}: campo(s) obrigatório(s) ausente(s): {', '.join(missing)}")
        sid = entry["id"]
        if not _ID_RE.match(sid):
            raise CatalogError(f"{where}: id '{sid}' não está em kebab-case")
        if sid in seen:
            raise CatalogError(f"{where}: id duplicado '{sid}'")
        if entry["kind"] not in KINDS:
            raise CatalogError(f"{where} ({sid}): kind '{entry['kind']}' fora de {KINDS}")
        if entry["tier"] not in TIER_WEIGHTS:
            raise CatalogError(f"{where} ({sid}): tier '{entry['tier']}' fora de {tuple(TIER_WEIGHTS)}")
        seen.add(sid)
        sources.append(
            Source(sid, entry["title"], entry["url"], entry["kind"], entry["tier"], entry.get("notes", ""))
        )
    return sources
