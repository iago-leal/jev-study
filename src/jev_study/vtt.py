"""Conversão de legendas WebVTT em texto com marcações de tempo (source-collection RF-04)."""

from __future__ import annotations

import html
import re

_CUE_RE = re.compile(r"^(\d{1,2}:)?(\d{2}):(\d{2})\.\d{3}\s+-->")
_TAG_RE = re.compile(r"<[^>]+>")
# Uma marcação a cada ~30 s de fala mantém o texto legível e a citação precisa.
MARK_EVERY_S = 30


def _seconds(line: str) -> int | None:
    m = _CUE_RE.match(line)
    if not m:
        return None
    hours = int(m.group(1)[:-1]) if m.group(1) else 0
    return hours * 3600 + int(m.group(2)) * 60 + int(m.group(3))


def vtt_to_text(vtt: str) -> str:
    """Remove cabeçalho, tags e as linhas repetidas típicas da legenda automática.

    O resultado intercala marcações `[t=SEGUNDOS]` no início de cada bloco.
    """
    out: list[str] = []
    last_line = ""
    last_mark = -MARK_EVERY_S
    current_start = 0
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE", "STYLE")):
            continue
        start = _seconds(line)
        if start is not None:
            current_start = start
            continue
        if line.isdigit():  # número de cue opcional
            continue
        text = html.unescape(_TAG_RE.sub("", line)).strip()
        if not text or text == last_line:
            continue
        if out and out[-1].endswith(text):
            continue
        if current_start - last_mark >= MARK_EVERY_S:
            out.append(f"\n[t={current_start}] ")
            last_mark = current_start
        out.append(text + " ")
        last_line = text
    return re.sub(r"[ \t]+", " ", "".join(out)).strip()
