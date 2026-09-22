"""Índice SQLite incremental e busca ponderada por tier (knowledge-index RF-04..RF-08)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np

from .chunking import chunk_document
from .config import EMBED_MODEL, TIER_WEIGHTS
from .embed import BatchFn, embed_documents, embed_query, ollama_batch
from .rawdoc import RawDocError, iter_docs

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, source_id TEXT, title TEXT, url TEXT,
  tier TEXT, kind TEXT, sha256 TEXT, indexed_at TEXT
);
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY, doc_id TEXT REFERENCES documents(id) ON DELETE CASCADE,
  ord INTEGER, text TEXT, start_s INTEGER, embedding BLOB
);
CREATE INDEX IF NOT EXISTS chunks_doc ON chunks(doc_id);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


class IndexStoreError(Exception):
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


@dataclass
class Hit:
    chunk_id: int
    doc_id: str
    source_id: str
    title: str
    url: str
    tier: str
    kind: str
    text: str
    start_s: int | None
    similarity: float
    score: float

    @property
    def cite_url(self) -> str:
        if self.kind == "youtube" and self.start_s:
            return f"{self.url}{'&' if '?' in self.url else '?'}t={self.start_s}s"
        return self.url


def _normalize(vec) -> np.ndarray:
    arr = np.asarray(vec, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    return arr / norm if norm else arr


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def update_index(
    conn: sqlite3.Connection,
    raw_dir: Path,
    *,
    batch_fn: BatchFn = ollama_batch,
    model: str = EMBED_MODEL,
    rebuild: bool = False,
    log: Callable[[str], None] = print,
) -> dict:
    stored_model = conn.execute("SELECT value FROM meta WHERE key='model'").fetchone()
    if stored_model and stored_model[0] != model and not rebuild:
        raise IndexStoreError(
            f"índice criado com '{stored_model[0]}', configurado '{model}': rode `jev index --rebuild`", exit_code=2
        )
    if rebuild:
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM documents")
        conn.commit()
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('model', ?)", (model,))
    conn.commit()

    known = dict(conn.execute("SELECT id, sha256 FROM documents").fetchall())
    stats = {"novos": 0, "atualizados": 0, "removidos": 0, "inalterados": 0, "avisos": 0}
    seen: set[str] = set()
    for path, doc in iter_docs(raw_dir):
        if isinstance(doc, RawDocError):
            log(f"aviso: {doc}")
            stats["avisos"] += 1
            continue
        seen.add(doc.id)
        if known.get(doc.id) == doc.sha256:
            stats["inalterados"] += 1
            continue
        chunks = chunk_document(doc.text, doc.kind)
        if not chunks:
            log(f"aviso: documento vazio, pulado: {doc.id}")
            stats["avisos"] += 1
            continue
        vectors = embed_documents([c.text for c in chunks], batch_fn, model=model)
        dim = len(vectors[0])
        # Um documento por transação: se o Ollama cair no meio, o que já foi gravado permanece.
        with conn:
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc.id,))
            conn.execute(
                "INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?,?)",
                (doc.id, doc.source_id, doc.title, doc.url, doc.tier, doc.kind, doc.sha256,
                 datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
            conn.executemany(
                "INSERT INTO chunks (doc_id, ord, text, start_s, embedding) VALUES (?,?,?,?,?)",
                [(doc.id, i, c.text, c.start_s, _normalize(v).tobytes()) for i, (c, v) in enumerate(zip(chunks, vectors))],
            )
            conn.execute("INSERT OR REPLACE INTO meta VALUES ('dim', ?)", (str(dim),))
        stats["atualizados" if doc.id in known else "novos"] += 1
        log(f"indexando {doc.id} ({len(chunks)} trechos)")

    orphans = [doc_id for doc_id in known if doc_id not in seen]
    with conn:
        for doc_id in orphans:
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    stats["removidos"] = len(orphans)
    stats["trechos"] = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    return stats


def chunk_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]


def search(
    conn: sqlite3.Connection,
    question: str,
    k: int,
    *,
    batch_fn: BatchFn = ollama_batch,
    model: str = EMBED_MODEL,
) -> list[Hit]:
    rows = conn.execute(
        "SELECT c.id, c.doc_id, d.source_id, d.title, d.url, d.tier, d.kind, c.text, c.start_s, c.embedding "
        "FROM chunks c JOIN documents d ON d.id = c.doc_id"
    ).fetchall()
    if not rows:
        return []
    matrix = np.stack([np.frombuffer(r[9], dtype=np.float32) for r in rows])
    query = _normalize(embed_query(question, batch_fn, model))
    sims = matrix @ query
    weights = np.array([TIER_WEIGHTS.get(r[5], 1.0) for r in rows], dtype=np.float32)
    scores = sims * weights
    # Desempate estável: pontuação, depois tier mais confiável.
    order = sorted(range(len(rows)), key=lambda i: (-float(scores[i]), -float(weights[i]), rows[i][0]))[:k]
    return [
        Hit(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], float(sims[i]), float(scores[i]))
        for i in order
        for r in [rows[i]]
    ]


def source_stats(conn: sqlite3.Connection) -> dict[str, int]:
    return dict(
        conn.execute(
            "SELECT d.source_id, COUNT(c.id) FROM documents d LEFT JOIN chunks c ON c.doc_id = d.id GROUP BY d.source_id"
        ).fetchall()
    )
