import json

from jev_study.catalog import Source
from jev_study.collect import collect, parse_llms_txt, slug_for
from jev_study.fetch import FetchError, Response
from jev_study.rawdoc import read_doc

LONG = "O Jev devolve decisões tipadas com probabilidade e confiança. " * 10


class FakeWeb:
    """Servidor simulado: url -> corpo (str) ou FetchError."""

    def __init__(self, pages: dict):
        self.pages = pages
        self.calls: list[str] = []

    def __call__(self, url: str) -> Response:
        self.calls.append(url)
        page = self.pages.get(url, FetchError("HTTP 404"))
        if isinstance(page, Exception):
            raise page
        ctype = "text/html" if page.lstrip().startswith("<") else "text/markdown"
        return Response(url, 200, ctype, page)


def _wayback_api(url: str) -> str:
    from urllib.parse import quote
    return "https://archive.org/wayback/available?url=" + quote(url, safe="")


def _run(tmp_path, sources, web, **kw):
    report = collect(sources, tmp_path / "raw", tmp_path / "report.json", fetch=web, log=lambda _m: None, **kw)
    return report


def test_web_ok(tmp_path):
    src = Source("blog", "Blog", "https://t.ai/blog", "web", "oficial")
    web = FakeWeb({src.url: f"<html><body><h1>Jev</h1><p>{LONG}</p></body></html>"})
    [entry] = _run(tmp_path, [src], web)
    assert entry["status"] == "ok" and entry["docs"] == 1
    doc = read_doc(tmp_path / "raw" / "blog.md")
    assert doc.via == "original" and "# Jev" in doc.text


def test_origem_fora_do_ar_recorre_ao_archive(tmp_path):
    src = Source("tc", "TechCrunch", "https://tc.com/a", "web", "imprensa")
    snap = "https://web.archive.org/web/20260920id_/https://tc.com/a"
    web = FakeWeb({
        src.url: FetchError("HTTP 503"),
        _wayback_api(src.url): json.dumps({"archived_snapshots": {"closest": {"available": True, "timestamp": "20260920", "url": "x"}}}),
        snap: f"<p>{LONG}</p>",
    })
    [entry] = _run(tmp_path, [src], web)
    assert entry["status"] == "archive"
    assert read_doc(tmp_path / "raw" / "tc.md").via == "archive"


def test_sem_snapshot_registra_motivo(tmp_path):
    src = Source("x", "X", "https://x.com/a", "web", "imprensa")
    web = FakeWeb({src.url: FetchError("timeout"), _wayback_api(src.url): json.dumps({"archived_snapshots": {}})})
    [entry] = _run(tmp_path, [src], web)
    assert entry["status"] == "falhou"
    assert "timeout" in entry["reason"] and "Internet Archive" in entry["reason"]


def test_llms_txt_so_mesmo_dominio_e_prefere_md(tmp_path):
    src = Source("docs", "Docs", "https://docs.t.ai/llms.txt", "llms_txt", "oficial")
    index = (
        "# TypeSafe\n\n"
        "- [Introdução](https://docs.t.ai/introduction): visão geral\n"
        "- [Perguntas](https://docs.t.ai/primitives/questions.md)\n"
        "- [Confiança](https://docs.t.ai/confidence)\n"
        "- [GitHub](https://github.com/typesafe)\n"
    ) + "\n" + ("texto do índice " * 20)
    web = FakeWeb({
        src.url: index,
        "https://docs.t.ai/introduction.md": LONG,
        "https://docs.t.ai/primitives/questions.md": LONG,
        "https://docs.t.ai/confidence.md": FetchError("HTTP 404"),
        "https://docs.t.ai/confidence": f"<html><body><p>{LONG}</p></body></html>",
    })
    [entry] = _run(tmp_path, [src], web)
    assert entry["docs"] == 3
    ids = sorted(p.relative_to(tmp_path / "raw").as_posix() for p in (tmp_path / "raw").rglob("*.md"))
    assert ids == ["docs/confidence.md", "docs/introduction.md", "docs/primitives-questions.md"]
    assert not any("github" in c for c in web.calls)


def test_parse_llms_txt_e_slug():
    links = parse_llms_txt("[A](https://d.io/a) [B](https://o.io/b) [A](https://d.io/a)", "https://d.io/llms.txt")
    assert links == [("A", "https://d.io/a")]
    assert slug_for("https://d.io/Guides/Quick_Start.md") == "guides-quick-start"


def test_idempotencia_e_refresh(tmp_path):
    src = Source("blog", "Blog", "https://t.ai/blog", "web", "oficial")
    web = FakeWeb({src.url: LONG})
    _run(tmp_path, [src], web)
    web.calls.clear()
    [entry] = _run(tmp_path, [src], web)
    assert entry["status"] == "pulado" and web.calls == []
    [entry] = _run(tmp_path, [src], web, refresh=True)
    assert entry["status"] == "ok" and web.calls == [src.url]


def test_relatorio_lista_cada_fonte_uma_vez(tmp_path):
    a = Source("a", "A", "https://a.io", "web", "oficial")
    b = Source("b", "B", "https://b.io", "web", "tecnica")
    v = Source("v", "V", "https://youtube.com/watch?v=1", "youtube", "oficial")
    web = FakeWeb({a.url: LONG, b.url: LONG})

    def no_subs(_url):
        raise FetchError("sem legenda disponível")

    _run(tmp_path, [a, b, v], web, youtube=no_subs)
    report = _run(tmp_path, [a, b, v], web, youtube=no_subs, only="b", refresh=True)
    assert [e["source_id"] for e in report] == ["a", "b", "v"]
    saved = json.loads((tmp_path / "report.json").read_text())
    assert {e["source_id"]: e["status"] for e in saved} == {"a": "ok", "b": "ok", "v": "falhou"}
    assert saved[2]["reason"] == "sem legenda disponível"


def test_youtube_grava_transcricao(tmp_path):
    v = Source("yt", "Vídeo", "https://www.youtube.com/watch?v=abc", "youtube", "oficial")
    [entry] = _run(tmp_path, [v], FakeWeb({}), youtube=lambda _u: ("Why We Made Jev", "[t=0] olá [t=30] mundo"))
    assert entry["status"] == "ok"
    doc = read_doc(tmp_path / "raw" / "yt.md")
    assert doc.title == "Why We Made Jev" and doc.kind == "youtube"
