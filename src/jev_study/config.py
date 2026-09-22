"""Caminhos e constantes compartilhados pelos componentes."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("JEV_STUDY_ROOT", Path.cwd()))
CATALOG_PATH = ROOT / "sources.toml"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REPORT_PATH = DATA_DIR / "collect-report.json"
INDEX_PATH = DATA_DIR / "index.db"
HISTORY_PATH = DATA_DIR / "history.jsonl"
EVAL_DIR = ROOT / "eval"

KINDS = ("web", "youtube", "llms_txt")
TIER_WEIGHTS = {"oficial": 1.00, "tecnica": 0.97, "imprensa": 0.93, "divulgacao": 0.88}

# Coleta
HTTP_TIMEOUT_S = 30
MIN_TEXT_CHARS = 200
LLMS_TXT_MAX_PAGES = 80
SAME_HOST_DELAY_S = 0.5
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36 jev-study/0.1 (uso pessoal de estudo)"
)

# Índice
CHUNK_MAX_CHARS = 1500
CHUNK_OVERLAP_CHARS = 200
# Multilíngue: perguntas em português contra acervo em inglês (nomic-embed-text falhava nisso).
EMBED_MODEL = os.environ.get("JEV_EMBED_MODEL", "bge-m3")
EMBED_BATCH = 32
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
EMBED_TIMEOUT_S = 60

# Consulta
DEFAULT_K = 6
DEFAULT_MODEL = "sonnet"
MIN_SCORE = 0.45  # bge-m3, 2026-09-22: só poupa cota (fora do tema 0,30–0,48, perguntas genéricas do tema ≈ 0,50: margem estreita); o prompt é quem recusa
CLAUDE_TIMEOUT_S = 180
