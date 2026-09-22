import pytest

from jev_study.catalog import CatalogError, parse_catalog
from jev_study.htmltext import html_to_text
from jev_study.rawdoc import Document, read_doc, write_doc
from jev_study.vtt import vtt_to_text


def _src(**over):
    base = {"id": "a", "title": "A", "url": "https://x.io", "kind": "web", "tier": "oficial"}
    return base | over


def test_catalog_valido():
    [s] = parse_catalog([_src(notes="n")])
    assert (s.id, s.kind, s.tier, s.notes) == ("a", "web", "oficial", "n")


@pytest.mark.parametrize(
    "entries, trecho",
    [
        ([_src(), _src()], "id duplicado"),
        ([_src(kind="pdf")], "kind"),
        ([_src(tier="blog")], "tier"),
        ([_src(url="")], "url"),
        ([_src(id="Com Espaco")], "kebab-case"),
    ],
)
def test_catalog_invalido(entries, trecho):
    with pytest.raises(CatalogError, match=trecho) as exc:
        parse_catalog(entries)
    assert "entrada" in str(exc.value)


def test_html_para_texto_remove_script_e_marca_titulos():
    html = """<html><head><title>Página</title><style>.x{}</style></head><body>
    <nav>menu</nav><h1>Jev</h1><p>Modelo <b>System One</b>.</p>
    <script>alert('x')</script><h2>Confiança</h2><ul><li>um</li><li>dois</li></ul>
    <footer>rodapé</footer></body></html>"""
    title, text = html_to_text(html)
    assert title == "Página"
    assert "alert" not in text and "menu" not in text and "rodapé" not in text
    assert "# Jev" in text and "## Confiança" in text
    assert "Modelo System One." in text
    assert "- um" in text


def test_vtt_sem_duplicatas_e_com_tempo():
    vtt = """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:03.000
hello <c>world</c>

00:00:03.000 --> 00:00:05.000
hello world

00:00:05.000 --> 00:00:07.000
jev is a system one model

00:00:40.000 --> 00:00:42.000
it returns probabilities
"""
    text = vtt_to_text(vtt)
    assert text.count("hello world") == 1
    assert text.startswith("[t=1]")
    assert "[t=40] it returns probabilities" in text


def test_documento_bruto_ida_e_volta(tmp_path):
    doc = Document("src/pagina", "src", 'Título com "aspas": e dois-pontos', "https://x.io/p", "oficial",
                   "llms_txt", "archive", "2026-09-22T00:00:00+00:00", "linha 1\n\n---\n\nlinha 2")
    path = write_doc(tmp_path, doc)
    assert path == tmp_path / "src" / "pagina.md"
    back = read_doc(path)
    assert back == doc
    assert len(back.sha256) == 64
