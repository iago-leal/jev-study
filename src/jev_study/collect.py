"""Orquestração da coleta por `kind`, com relatório (source-collection RF-02..RF-08)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .catalog import Source
from .config import LLMS_TXT_MAX_PAGES, MIN_TEXT_CHARS
from .fetch import Fetcher, FetchError, http_get, wayback_snapshot_url
from .htmltext import html_to_text, looks_like_html
from .rawdoc import Document, doc_path, write_doc
from .vtt import vtt_to_text

YoutubeFn = Callable[[str], tuple[str, str]]  # url -> (título, texto com [t=N])

_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_SUB_PREFERENCE = ("en", "en-US", "en-GB", "pt-BR", "pt", "en-orig", "pt-orig")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_text(body: str, content_type: str) -> str:
    if "html" in content_type or looks_like_html(body):
        return html_to_text(body)[1]
    return body.strip()


def fetch_text(url: str, fetch: Fetcher, allow_archive: bool = True) -> tuple[str, str]:
    """Devolve (texto, via). Recorre ao Internet Archive se a origem falhar ou vier curta."""
    try:
        resp = fetch(url)
        text = _to_text(resp.body, resp.content_type)
        if len(text) >= MIN_TEXT_CHARS:
            return text, "original"
        reason = f"texto curto na origem ({len(text)} caracteres)"
    except FetchError as exc:
        reason = str(exc)
    if not allow_archive:
        raise FetchError(reason)
    snapshot = wayback_snapshot_url(url, fetch)
    if not snapshot:
        raise FetchError(f"{reason}; sem snapshot no Internet Archive")
    try:
        resp = fetch(snapshot)
    except FetchError as exc:
        raise FetchError(f"{reason}; Internet Archive: {exc}") from None
    text = _to_text(resp.body, resp.content_type)
    if len(text) < MIN_TEXT_CHARS:
        raise FetchError(f"{reason}; snapshot também curto ({len(text)} caracteres)")
    return text, "archive"


def parse_llms_txt(index: str, base_url: str) -> list[tuple[str, str]]:
    """Links Markdown do mesmo host do índice, sem repetição, na ordem em que aparecem."""
    host = urllib.parse.urlsplit(base_url).netloc
    seen: set[str] = set()
    links: list[tuple[str, str]] = []
    for title, url in _MD_LINK_RE.findall(index):
        if urllib.parse.urlsplit(url).netloc != host or url in seen:
            continue
        seen.add(url)
        links.append((title.strip(), url))
    return links


def slug_for(url: str) -> str:
    path = urllib.parse.urlsplit(url).path.strip("/")
    path = re.sub(r"\.(md|mdx|txt|html?)$", "", path)
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    return slug or "index"


def youtube_transcript(url: str) -> tuple[str, str]:
    """Título e transcrição via yt-dlp, sem baixar o vídeo."""
    if not shutil.which("yt-dlp"):
        raise FetchError("yt-dlp não encontrado no PATH")
    last_error = "sem legenda disponível"
    with tempfile.TemporaryDirectory() as tmp:
        info_path = Path(tmp, "video.info.json")
        # Um idioma por chamada: pedir vários de uma vez provoca HTTP 429 no YouTube.
        for lang in _SUB_PREFERENCE:
            cmd = [
                "yt-dlp", "--no-update", "--skip-download", "--write-info-json",
                "--write-subs", "--write-auto-subs", "--sub-langs", lang, "--sub-format", "vtt",
                "-o", os.path.join(tmp, "video.%(ext)s"), url,
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            except subprocess.TimeoutExpired:
                raise FetchError("yt-dlp: timeout") from None
            sub_path = Path(tmp, f"video.{lang}.vtt")
            if sub_path.exists():
                text = vtt_to_text(sub_path.read_text(encoding="utf-8"))
                if text:
                    title = json.loads(info_path.read_text(encoding="utf-8")).get("title", url) if info_path.exists() else url
                    return title, text
            elif proc.returncode != 0:
                last_error = (proc.stderr.strip().splitlines() or ["erro desconhecido"])[-1]
                if "429" in last_error or "Unsupported URL" in last_error or "unavailable" in last_error.lower():
                    break
        if last_error != "sem legenda disponível":
            raise FetchError(f"yt-dlp: {last_error} (tente `brew upgrade yt-dlp` ou recolete mais tarde)")
        raise FetchError("sem legenda disponível")


def _entry(src: Source, status: str, docs: int = 0, reason: str = "", warnings: list[str] | None = None) -> dict:
    return {
        "source_id": src.id, "title": src.title, "kind": src.kind, "tier": src.tier,
        "status": status, "docs": docs, "reason": reason, "warnings": warnings or [], "at": _now(),
    }


def _already_collected(src: Source, raw_dir: Path) -> int:
    if src.kind == "llms_txt":
        folder = raw_dir / src.id
        return len(list(folder.glob("*.md"))) if folder.is_dir() else 0
    return 1 if doc_path(raw_dir, src.id).exists() else 0


def _collect_web(src: Source, raw_dir: Path, fetch: Fetcher) -> dict:
    text, via = fetch_text(src.url, fetch)
    write_doc(raw_dir, Document(src.id, src.id, src.title, src.url, src.tier, src.kind, via, _now(), text))
    return _entry(src, "ok" if via == "original" else "archive", 1)


def _collect_youtube(src: Source, raw_dir: Path, youtube: YoutubeFn) -> dict:
    title, text = youtube(src.url)
    write_doc(raw_dir, Document(src.id, src.id, title or src.title, src.url, src.tier, src.kind, "original", _now(), text))
    return _entry(src, "ok", 1)


def _collect_llms_txt(src: Source, raw_dir: Path, fetch: Fetcher) -> dict:
    index, via = fetch_text(src.url, fetch)
    links = parse_llms_txt(index, src.url)
    warnings: list[str] = []
    if len(links) > LLMS_TXT_MAX_PAGES:
        warnings.append(f"índice com {len(links)} links; coletados os {LLMS_TXT_MAX_PAGES} primeiros")
        links = links[:LLMS_TXT_MAX_PAGES]
    written, used_archive = 0, via == "archive"
    for link_title, url in links:
        candidates = [url] if re.search(r"\.(md|txt)$", url) else [url + ".md", url]
        text, page_via, last_err = None, "original", ""
        for i, candidate in enumerate(candidates):
            try:
                # A variante .md não passa pelo Internet Archive; a URL canônica, sim.
                text, page_via = fetch_text(candidate, fetch, allow_archive=(i == len(candidates) - 1))
                break
            except FetchError as exc:
                last_err = str(exc)
        if text is None:
            warnings.append(f"{url}: {last_err}")
            continue
        used_archive |= page_via == "archive"
        doc_id = f"{src.id}/{slug_for(url)}"
        write_doc(raw_dir, Document(doc_id, src.id, f"{src.title}: {link_title}", url, src.tier, src.kind, page_via, _now(), text))
        written += 1
    if not written:
        raise FetchError("nenhuma página do índice pôde ser coletada" + (f" ({warnings[-1]})" if warnings else ""))
    return _entry(src, "archive" if used_archive else "ok", written, warnings=warnings)


def collect(
    sources: list[Source],
    raw_dir: Path,
    report_path: Path,
    *,
    fetch: Fetcher = http_get,
    youtube: YoutubeFn = youtube_transcript,
    refresh: bool = False,
    only: str | None = None,
    log: Callable[[str], None] = print,
) -> list[dict]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    previous = {}
    if report_path.exists():
        try:
            previous = {e["source_id"]: e for e in json.loads(report_path.read_text(encoding="utf-8"))}
        except (json.JSONDecodeError, KeyError, TypeError):
            previous = {}
    selected = [s for s in sources if only is None or s.id == only]
    report: list[dict] = []
    for n, src in enumerate(sources, start=1):
        if src not in selected:
            report.append(previous.get(src.id) or _entry(src, "pulado", reason="fora do filtro --only"))
            continue
        existing = _already_collected(src, raw_dir)
        if existing and not refresh:
            entry = _entry(src, "pulado", existing, reason="já coletado (use --refresh)")
        else:
            try:
                if src.kind == "web":
                    entry = _collect_web(src, raw_dir, fetch)
                elif src.kind == "youtube":
                    entry = _collect_youtube(src, raw_dir, youtube)
                else:
                    entry = _collect_llms_txt(src, raw_dir, fetch)
            except FetchError as exc:
                entry = _entry(src, "falhou", reason=str(exc))
        log(f"[{n}/{len(sources)}] {src.id} ... {entry['status']}" + (f" ({entry['reason']})" if entry["reason"] else ""))
        report.append(entry)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = report_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, report_path)
    return report


def format_report(report: list[dict]) -> str:
    width = max((len(e["source_id"]) for e in report), default=10)
    lines = [f"{'fonte':<{width}}  {'status':<8} docs  motivo", "-" * (width + 30)]
    for e in report:
        lines.append(f"{e['source_id']:<{width}}  {e['status']:<8} {e['docs']:>4}  {e['reason']}")
        lines.extend(f"{'':<{width}}  {'':<8}       aviso: {w}" for w in e.get("warnings", [])[:5])
    counts = {s: sum(1 for e in report if e["status"] == s) for s in ("ok", "archive", "falhou", "pulado")}
    lines.append("")
    lines.append("  ".join(f"{k}: {v}" for k, v in counts.items()))
    return "\n".join(lines)
