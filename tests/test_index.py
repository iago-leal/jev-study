import numpy as np
import pytest

from jev_study.chunking import chunk_document, split_text, strip_blobs
from jev_study.embed import EmbedError, embed_documents, prefixes
from jev_study.index import IndexStoreError, connect, search, update_index
from jev_study.rawdoc import Document, write_doc

VOCAB = ["jev", "confiança", "probabilidade", "decisão", "llm", "token", "mongólia", "capital"]


class FakeEmbedder:
    """Embedding por contagem de palavras do vocabulário: determinístico e sem Ollama."""

    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, texts):
        self.calls.append(list(texts))
        out = []
        for t in texts:
            low = t.lower()
            vec = [float(low.count(w)) for w in VOCAB] + [0.01]
            out.append(vec)
        return out


def _doc(doc_id, text, tier="oficial", kind="web", url=None):
    return Document(doc_id, doc_id.split("/")[0], doc_id.upper(), url or f"https://x.io/{doc_id}", tier, kind,
                    "original", "2026-09-22T00:00:00+00:00", text)


def test_fragmentacao_respeita_limite_e_sobreposicao():
    paras = [("Parágrafo %d. " % i) + "palavra " * 60 for i in range(8)]
    text = "\n\n".join(paras)
    assert 3900 < len(text) < 4100
    chunks = split_text(text, 1500, 200)
    assert 3 <= len(chunks) <= 4
    assert all(len(c) <= 1500 for c in chunks)
    # A sobreposição repete o fim do trecho anterior no início do seguinte.
    assert chunks[0][-50:].split()[-1] in chunks[1][:250]


def test_fragmentacao_de_paragrafo_unico_gigante():
    chunks = split_text("x" * 4000, 1500, 200)
    assert all(len(c) <= 1500 for c in chunks) and len(chunks) >= 3


def test_youtube_start_s_e_remocao_das_marcacoes():
    text = "[t=0] abertura " + "fala " * 250 + "\n[t=125] " + "tema " * 250
    chunks = chunk_document(text, "youtube", 1500, 200)
    assert chunks[0].start_s == 0
    assert any(c.start_s == 125 for c in chunks)
    assert all("[t=" not in c.text for c in chunks)


def test_embed_prefixos_e_lotes():
    fake = FakeEmbedder()
    embed_documents([f"t{i}" for i in range(70)], fake, batch_size=32, model="nomic-embed-text")
    assert [len(c) for c in fake.calls] == [32, 32, 6]
    assert all(t.startswith("search_document: ") for c in fake.calls for t in c)
    assert prefixes("nomic-embed-text:latest")[1] == "search_query: "
    assert prefixes("bge-m3") == ("", "")


def test_indice_incremental_normalizado_e_orfaos(tmp_path):
    raw = tmp_path / "raw"
    write_doc(raw, _doc("a", "Jev devolve confiança e probabilidade."))
    write_doc(raw, _doc("b", "LLM gera token a token."))
    conn = connect(tmp_path / "index.db")
    fake = FakeEmbedder()
    stats = update_index(conn, raw, batch_fn=fake, log=lambda _m: None)
    assert stats["novos"] == 2 and stats["trechos"] == 2
    blob = conn.execute("SELECT embedding FROM chunks LIMIT 1").fetchone()[0]
    assert abs(np.linalg.norm(np.frombuffer(blob, dtype=np.float32)) - 1) < 1e-5

    fake.calls.clear()
    stats = update_index(conn, raw, batch_fn=fake, log=lambda _m: None)
    assert fake.calls == [] and stats["inalterados"] == 2

    (raw / "b.md").unlink()
    write_doc(raw, _doc("a", "Jev: decisão com confiança."))
    stats = update_index(conn, raw, batch_fn=fake, log=lambda _m: None)
    assert (stats["atualizados"], stats["removidos"], stats["trechos"]) == (1, 1, 1)


def test_troca_de_modelo_exige_rebuild(tmp_path):
    raw = tmp_path / "raw"
    write_doc(raw, _doc("a", "Jev"))
    conn = connect(tmp_path / "index.db")
    update_index(conn, raw, batch_fn=FakeEmbedder(), log=lambda _m: None)
    with pytest.raises(IndexStoreError) as exc:
        update_index(conn, raw, batch_fn=FakeEmbedder(), model="outro", log=lambda _m: None)
    assert exc.value.exit_code == 2
    update_index(conn, raw, batch_fn=FakeEmbedder(), model="outro", rebuild=True, log=lambda _m: None)


def test_busca_ordena_por_pontuacao_e_desempata_por_tier(tmp_path):
    raw = tmp_path / "raw"
    write_doc(raw, _doc("oficial", "Jev confiança", tier="oficial"))
    write_doc(raw, _doc("divulga", "Jev confiança", tier="divulgacao"))
    write_doc(raw, _doc("outro", "capital da mongólia", tier="oficial"))
    conn = connect(tmp_path / "index.db")
    fake = FakeEmbedder()
    update_index(conn, raw, batch_fn=fake, log=lambda _m: None)
    fake.calls.clear()
    hits = search(conn, "confiança do jev", 3, batch_fn=fake, model="nomic-embed-text")
    assert fake.calls[0][0].startswith("search_query: ")
    assert [h.doc_id for h in hits[:2]] == ["oficial", "divulga"]
    assert hits[0].similarity == pytest.approx(hits[1].similarity)
    assert hits[0].score > hits[1].score > hits[2].score


def test_url_de_citacao_do_youtube(tmp_path):
    raw = tmp_path / "raw"
    text = "[t=0] intro " + "fala " * 300 + "\n[t=95] " + "Jev confiança " * 100
    write_doc(raw, _doc("yt", text, kind="youtube", url="https://www.youtube.com/watch?v=abc"))
    conn = connect(tmp_path / "index.db")
    update_index(conn, raw, batch_fn=FakeEmbedder(), log=lambda _m: None)
    [hit] = search(conn, "jev confiança", 1, batch_fn=FakeEmbedder())
    assert hit.start_s == 95
    assert hit.cite_url == "https://www.youtube.com/watch?v=abc&t=95s"


def test_ollama_fora_do_ar_mantem_o_que_ja_foi_gravado(tmp_path):
    raw = tmp_path / "raw"
    write_doc(raw, _doc("a", "Jev"))
    write_doc(raw, _doc("b", "LLM"))
    conn = connect(tmp_path / "index.db")
    calls = {"n": 0}

    def flaky(texts):
        calls["n"] += 1
        if calls["n"] > 1:
            raise EmbedError("Ollama indisponível")
        return FakeEmbedder()(texts)

    with pytest.raises(EmbedError):
        update_index(conn, raw, batch_fn=flaky, log=lambda _m: None)
    assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 1


def test_descarta_base64_e_data_uri():
    blob = "iVBORw0KGgoAAAANSUhEUgAA" * 20
    text = f"Resultado do cookbook ![img](data:image/png;base64,{blob}) e o hash {blob[:120]} fim."
    clean = strip_blobs(text)
    assert "iVBOR" not in clean and "Resultado do cookbook" in clean and "fim." in clean
    assert chunk_document(blob * 10, "web") == []
    share = "https://console.typesafe.ai/playground#share/" + "N4Ig" * 300
    assert strip_blobs(f'<a href="{share}">abrir</a>') == '<a href="https://console.typesafe.ai/playground">abrir</a>'
    # URLs longas continuam intactas.
    url = "https://docs.typesafe.ai/cookbooks/" + "a" * 90
    assert url in strip_blobs(f"veja {url} aqui")
