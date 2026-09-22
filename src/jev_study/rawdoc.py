"""Documentos brutos em `data/raw/<id>.md` com cabeçalho (source-collection RF-06)."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

FIELDS = ("id", "source_id", "title", "url", "tier", "kind", "via", "fetched_at", "sha256")


class RawDocError(Exception):
    pass


@dataclass
class Document:
    id: str
    source_id: str
    title: str
    url: str
    tier: str
    kind: str
    via: str
    fetched_at: str
    text: str
    sha256: str = ""

    def __post_init__(self) -> None:
        if not self.sha256:
            self.sha256 = hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def doc_path(raw_dir: Path, doc_id: str) -> Path:
    return raw_dir / f"{doc_id}.md"


def write_doc(raw_dir: Path, doc: Document) -> Path:
    path = doc_path(raw_dir, doc.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = asdict(doc)
    # Valores em JSON: YAML válido e sem ambiguidade de escape.
    header = "\n".join(f"{k}: {json.dumps(meta[k], ensure_ascii=False)}" for k in FIELDS)
    content = f"---\n{header}\n---\n\n{doc.text}\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.replace(tmp, path)
    return path


def read_doc(path: Path) -> Document:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise RawDocError(f"cabeçalho ausente em {path}")
    end = content.find("\n---\n", 4)
    if end < 0:
        raise RawDocError(f"cabeçalho sem fechamento em {path}")
    meta: dict[str, str] = {}
    for line in content[4:end].splitlines():
        key, sep, value = line.partition(": ")
        if not sep:
            raise RawDocError(f"linha de cabeçalho inválida em {path}: {line!r}")
        try:
            meta[key] = json.loads(value)
        except json.JSONDecodeError:
            raise RawDocError(f"valor inválido para '{key}' em {path}") from None
    missing = [f for f in FIELDS if f not in meta]
    if missing:
        raise RawDocError(f"campos ausentes em {path}: {', '.join(missing)}")
    text = content[end + 5 :].strip("\n")
    return Document(text=text, **{k: meta[k] for k in FIELDS})


def iter_docs(raw_dir: Path):
    """Percorre data/raw/ em ordem estável, devolvendo (caminho, Document | RawDocError)."""
    for path in sorted(raw_dir.rglob("*.md")):
        try:
            yield path, read_doc(path)
        except RawDocError as exc:
            yield path, exc
