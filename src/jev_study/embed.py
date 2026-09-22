"""Cliente de embeddings do Ollama (knowledge-index RF-03)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable

from .config import EMBED_BATCH, EMBED_MODEL, EMBED_TIMEOUT_S, OLLAMA_URL

# Prefixos de tarefa (documento, pergunta) por modelo. O nomic-embed-text foi treinado com eles;
# o bge-m3 dispensa prefixo.
TASK_PREFIXES = {
    "nomic-embed-text": ("search_document: ", "search_query: "),
}


def prefixes(model: str = EMBED_MODEL) -> tuple[str, str]:
    return TASK_PREFIXES.get(model.split(":")[0], ("", ""))


BatchFn = Callable[[list[str]], list[list[float]]]


class EmbedError(Exception):
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


def ollama_batch(texts: list[str], model: str | None = None, base_url: str = OLLAMA_URL) -> list[list[float]]:
    model = model or EMBED_MODEL
    payload = json.dumps({"model": model, "input": texts}).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/api/embed", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=EMBED_TIMEOUT_S) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        if exc.code == 404 or "not found" in body:
            raise EmbedError(f"modelo '{model}' ausente no Ollama: rode `ollama pull {model}`") from None
        raise EmbedError(f"Ollama devolveu HTTP {exc.code}: {body[:200]}") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        raise EmbedError(f"Ollama indisponível em {base_url}; inicie-o com `ollama serve`") from None
    vectors = data.get("embeddings")
    if not vectors or len(vectors) != len(texts):
        raise EmbedError("resposta do Ollama sem embeddings válidos")
    return vectors


def embed_documents(
    texts: list[str], batch_fn: BatchFn = ollama_batch, batch_size: int = EMBED_BATCH, model: str = EMBED_MODEL
) -> list[list[float]]:
    doc_prefix = prefixes(model)[0]
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        vectors.extend(batch_fn([doc_prefix + t for t in texts[i : i + batch_size]]))
    return vectors


def embed_query(question: str, batch_fn: BatchFn = ollama_batch, model: str = EMBED_MODEL) -> list[float]:
    return batch_fn([prefixes(model)[1] + question])[0]
