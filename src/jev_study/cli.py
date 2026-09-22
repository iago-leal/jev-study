"""CLI `jev`: collect, index, search, ask, sources, eval."""

from __future__ import annotations

import argparse
import json
import sys
import time

from . import config
from .ask import AskError, answer_question, append_history, format_result
from .catalog import CatalogError, load_catalog
from .collect import collect, format_report
from .embed import EmbedError
from .evaluate import load_questions, run_eval
from .index import IndexStoreError, chunk_count, connect, search, source_stats, update_index


def _err(msg: str, code: int) -> int:
    print(f"erro: {msg}", file=sys.stderr)
    return code


def cmd_collect(args) -> int:
    try:
        sources = load_catalog(config.CATALOG_PATH)
    except CatalogError as exc:
        return _err(str(exc), 2)
    if not sources:
        print("Catálogo vazio: edite sources.toml")
        return 0
    if args.only and args.only not in {s.id for s in sources}:
        return _err(f"fonte '{args.only}' não existe no catálogo", 2)
    try:
        report = collect(sources, config.RAW_DIR, config.REPORT_PATH, refresh=args.refresh, only=args.only)
    except OSError as exc:
        return _err(f"falha de escrita em {exc.filename or config.DATA_DIR}: {exc.strerror}", 1)
    print()
    print(format_report(report))
    return 0


def cmd_index(args) -> int:
    if not config.RAW_DIR.exists() or not any(config.RAW_DIR.rglob("*.md")):
        print("Acervo vazio: rode jev collect")
        return 0
    conn = connect(config.INDEX_PATH)
    try:
        stats = update_index(conn, config.RAW_DIR, rebuild=args.rebuild)
    except (EmbedError, IndexStoreError) as exc:
        return _err(str(exc), exc.exit_code)
    print()
    print("  ".join(f"{k}: {v}" for k, v in stats.items()))
    return 0


def _open_index():
    if not config.INDEX_PATH.exists():
        return None
    conn = connect(config.INDEX_PATH)
    return conn if chunk_count(conn) else None


def cmd_search(args) -> int:
    conn = _open_index()
    if conn is None:
        print("Índice vazio: rode jev index")
        return 0
    try:
        t0 = time.perf_counter()
        hits = search(conn, args.question, args.k)
        elapsed = time.perf_counter() - t0
    except EmbedError as exc:
        return _err(str(exc), exc.exit_code)
    for n, h in enumerate(hits, start=1):
        preview = " ".join(h.text.split())[:300]
        print(f"[{n}] {h.score:.3f}  {h.title} [{h.tier}]\n    {h.cite_url}\n    {preview}\n")
    print(f"({len(hits)} trechos em {elapsed:.2f} s)")
    return 0


def _ask_one(conn, question: str, args):
    hits = search(conn, question, args.k)
    return answer_question(question, hits, model=args.model, min_score=args.min_score)


def cmd_ask(args) -> int:
    question = " ".join(args.question).strip()
    if not question:
        return _err("pergunta vazia", 2)
    conn = _open_index()
    if conn is None:
        print("Índice vazio: rode jev collect e jev index")
        return 0
    print("consultando o acervo...", file=sys.stderr)
    try:
        hits = search(conn, question, args.k)
    except EmbedError as exc:
        return _err(str(exc), exc.exit_code)
    if args.show_context:
        for n, h in enumerate(hits, start=1):
            print(f"--- [{n}] {h.score:.3f} {h.title} [{h.tier}] {h.cite_url}\n{h.text}\n")
    if hits and hits[0].score >= args.min_score:
        print(f"gerando resposta com {args.model}...", file=sys.stderr)
    try:
        result = answer_question(question, hits, model=args.model, min_score=args.min_score)
    except AskError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        print("\nTrechos recuperados (sem síntese):")
        for n, h in enumerate(exc.hits, start=1):
            print(f"[{n}] {h.title} [{h.tier}] {h.cite_url}\n    {' '.join(h.text.split())[:300]}")
        return exc.exit_code
    print(format_result(result))
    append_history(config.HISTORY_PATH, result)
    return 0


def cmd_sources(args) -> int:
    try:
        sources = load_catalog(config.CATALOG_PATH)
    except CatalogError as exc:
        return _err(str(exc), 2)
    report = {}
    if config.REPORT_PATH.exists():
        report = {e["source_id"]: e for e in json.loads(config.REPORT_PATH.read_text(encoding="utf-8"))}
    chunks = {}
    if config.INDEX_PATH.exists():
        chunks = source_stats(connect(config.INDEX_PATH))
    width = max(len(s.id) for s in sources) if sources else 10
    print(f"{'fonte':<{width}}  {'tier':<10} {'kind':<8} {'coleta':<8} trechos  título")
    for s in sources:
        status = report.get(s.id, {}).get("status", "-")
        print(f"{s.id:<{width}}  {s.tier:<10} {s.kind:<8} {status:<8} {chunks.get(s.id, 0):>7}  {s.title}")
    return 0


def cmd_eval(args) -> int:
    qpath = config.ROOT / args.file if args.file else config.EVAL_DIR / "questions.txt"
    if not qpath.exists():
        return _err(f"arquivo de perguntas não encontrado: {qpath}", 2)
    conn = _open_index()
    if conn is None:
        print("Índice vazio: rode jev collect e jev index")
        return 0
    questions = load_questions(qpath)
    try:
        path, cited, total = run_eval(questions, lambda q: _ask_one(conn, q, args), config.EVAL_DIR)
    except EmbedError as exc:
        return _err(str(exc), exc.exit_code)
    pct = 100 * cited / total if total else 0
    print(f"Respostas com ao menos uma citação: {cited}/{total} ({pct:.0f}%)")
    print(f"Relatório para conferência: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jev", description="Acervo local e RAG leve sobre o Jev (TypeSafe AI).")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="coleta as fontes de sources.toml para data/raw/")
    c.add_argument("--refresh", action="store_true", help="recoleta mesmo o que já existe")
    c.add_argument("--only", metavar="ID", help="coleta só esta fonte")
    c.set_defaults(func=cmd_collect)

    i = sub.add_parser("index", help="fragmenta e indexa data/raw/ com embeddings locais")
    i.add_argument("--rebuild", action="store_true", help="recria o índice do zero")
    i.set_defaults(func=cmd_index)

    def add_query_opts(sp):
        sp.add_argument("-k", type=int, default=config.DEFAULT_K, help=f"trechos recuperados (padrão {config.DEFAULT_K})")

    s = sub.add_parser("search", help="busca semântica sem gerar resposta")
    s.add_argument("question")
    add_query_opts(s)
    s.set_defaults(func=cmd_search)

    def add_answer_opts(sp):
        add_query_opts(sp)
        sp.add_argument("--model", default=config.DEFAULT_MODEL, help=f"alias do modelo no claude (padrão {config.DEFAULT_MODEL})")
        sp.add_argument("--min-score", type=float, default=config.MIN_SCORE, help=f"limiar de recusa (padrão {config.MIN_SCORE})")

    a = sub.add_parser("ask", help="pergunta ao acervo; resposta com citações via claude -p")
    a.add_argument("question", nargs="+")
    add_answer_opts(a)
    a.add_argument("--show-context", action="store_true", help="mostra os trechos enviados ao modelo")
    a.set_defaults(func=cmd_ask)

    so = sub.add_parser("sources", help="lista o catálogo com status de coleta e trechos indexados")
    so.set_defaults(func=cmd_sources)

    e = sub.add_parser("eval", help="roda eval/questions.txt e grava relatório para conferência")
    e.add_argument("file", nargs="?", help="arquivo de perguntas (padrão eval/questions.txt)")
    add_answer_opts(e)
    e.set_defaults(func=cmd_eval)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "k", 1) < 1:
        return _err("-k deve ser ≥ 1", 2)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
