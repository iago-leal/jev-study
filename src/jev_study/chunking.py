"""Fragmentação com sobreposição e tempo de início em vídeos (knowledge-index RF-01, RF-02)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS

_MARK_RE = re.compile(r"\[t=(\d+)\]\s*")
_SEPARATORS = ("\n\n", "\n", ". ", " ")
# Imagens e dados embutidos nos cookbooks (data: URIs, base64, hashes longos) só poluem a busca.
_DATA_URI_RE = re.compile(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+")
# Só tokens isolados (após espaço, aspas, parêntese...): trechos longos dentro de URLs ficam intactos.
_BLOB_RE = re.compile(r"(?:^|(?<=[\s\"'(\[,:=>]))[A-Za-z0-9+/=_-]{80,}(?=$|[\s\"')\],<.])", re.MULTILINE)
# Links de compartilhamento do playground carregam o estado inteiro no fragmento (milhares de caracteres).
_URL_PAYLOAD_RE = re.compile(r"(https?://[^\s\"'<>()#?]+)[#?][^\s\"'<>()]{80,}")
MIN_CHUNK_CHARS = 1  # descarta só trechos que ficaram vazios após a limpeza


@dataclass
class Chunk:
    text: str
    start_s: int | None = None


def _split_units(text: str, max_chars: int, seps: tuple[str, ...] = _SEPARATORS) -> list[str]:
    """Quebra o texto em unidades ≤ max_chars, preferindo parágrafo, linha, frase e palavra."""
    if len(text) <= max_chars:
        return [text] if text.strip() else []
    if not seps:
        return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
    sep, rest = seps[0], seps[1:]
    pieces = text.split(sep)
    units: list[str] = []
    for i, piece in enumerate(pieces):
        piece = piece + (sep if i < len(pieces) - 1 and sep.strip() else "")
        units.extend(_split_units(piece, max_chars, rest) if len(piece) > max_chars else ([piece] if piece.strip() else []))
    return units


def _tail(text: str, n: int) -> str:
    if n <= 0 or len(text) <= n:
        return "" if n <= 0 else text
    cut = text[-n:]
    space = cut.find(" ")
    return cut[space + 1 :] if 0 <= space < n // 2 else cut


def split_text(text: str, max_chars: int = CHUNK_MAX_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    units = _split_units(text.strip(), max_chars)
    chunks: list[str] = []
    current = ""
    for unit in units:
        joiner = "\n\n" if current and not current.endswith((" ", "\n")) else ""
        if current and len(current) + len(joiner) + len(unit) > max_chars:
            chunks.append(current.strip())
            carry = _tail(current.strip(), overlap)
            current = carry + " " + unit if carry and len(carry) + 1 + len(unit) <= max_chars else unit
        else:
            current = current + joiner + unit
    if current.strip():
        chunks.append(current.strip())
    return chunks


def strip_blobs(text: str) -> str:
    text = _DATA_URI_RE.sub("", text)
    text = _URL_PAYLOAD_RE.sub(r"\1", text)
    return _BLOB_RE.sub("", text)


def chunk_document(text: str, kind: str, max_chars: int = CHUNK_MAX_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[Chunk]:
    text = strip_blobs(text)
    if kind != "youtube":
        return [Chunk(t) for t in split_text(text, max_chars, overlap) if len(t) >= MIN_CHUNK_CHARS]
    out: list[Chunk] = []
    last_mark: int | None = 0
    for piece in split_text(text, max_chars, overlap):
        marks = [int(m) for m in _MARK_RE.findall(piece)]
        # Sem marcação no trecho, vale a última vista (o trecho continua a fala anterior).
        start = marks[0] if marks else last_mark
        if marks:
            last_mark = marks[-1]
        clean = _MARK_RE.sub("", piece).strip()
        if len(clean) >= MIN_CHUNK_CHARS:
            out.append(Chunk(clean, start))
    return out
