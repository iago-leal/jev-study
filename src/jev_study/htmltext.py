"""Conversão de HTML em texto legível (source-collection RF-02)."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser

_SKIP = {"script", "style", "nav", "footer", "header", "noscript", "svg", "form", "aside", "template"}
_BLOCK = {
    "p", "div", "section", "article", "main", "li", "ul", "ol", "br", "tr", "table",
    "blockquote", "pre", "figure", "figcaption", "dd", "dt", "h4", "h5", "h6",
}
_HEADINGS = {"h1": "# ", "h2": "## ", "h3": "### "}
_VOID = {"br", "img", "hr", "meta", "link", "input", "source", "wbr"}


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            if tag not in _VOID:
                self.skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if self.skip_depth:
            return
        if tag in _HEADINGS:
            self.parts.append("\n\n" + _HEADINGS[tag])
        elif tag in _BLOCK:
            self.parts.append("\n\n" if tag != "li" else "\n- ")

    def handle_endtag(self, tag):
        if tag in _SKIP and tag not in _VOID:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if tag == "title":
            self._in_title = False
        if not self.skip_depth and (tag in _HEADINGS or tag in _BLOCK):
            self.parts.append("\n\n")

    def handle_data(self, data):
        if self._in_title and not self.title:
            self.title = data.strip()
        if self.skip_depth or self._in_title:
            return
        self.parts.append(data)


def html_to_text(markup: str) -> tuple[str, str]:
    """Devolve (título da página, texto). Títulos h1–h3 saem prefixados por '#'."""
    parser = _Extractor()
    parser.feed(markup)
    parser.close()
    raw = html.unescape("".join(parser.parts))
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in raw.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = re.sub(r"^(#+) *\n+", r"\1 ", text, flags=re.MULTILINE)
    return parser.title, text


def looks_like_html(body: str) -> bool:
    head = body[:1000].lower()
    return "<html" in head or "<!doctype html" in head or "<body" in head
