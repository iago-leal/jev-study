import json

import pytest

from jev_study.ask import (
    AskError,
    answer_question,
    append_history,
    build_prompt,
    cited_numbers,
    claude_argv,
    format_result,
)
from jev_study.cli import build_parser
from jev_study.evaluate import run_eval
from jev_study.index import Hit


def _hit(n, score=0.8, tier="oficial", kind="web", start_s=None):
    url = "https://www.youtube.com/watch?v=abc" if kind == "youtube" else f"https://x.io/{n}"
    return Hit(n, f"doc{n}", "src", f"Título {n}", url, tier, kind, f"texto {n}", start_s, score, score)


class FakeClaude:
    def __init__(self, answer="O Jev decide [1] e calibra [3]."):
        self.answer = answer
        self.calls = []

    def __call__(self, argv, stdin):
        self.calls.append((argv, stdin))
        return self.answer


def test_abaixo_do_limiar_nao_chama_o_modelo():
    fake = FakeClaude()
    result = answer_question("capital da Mongólia?", [_hit(1, 0.3), _hit(2, 0.2)], model="sonnet", min_score=0.5, runner=fake)
    assert fake.calls == [] and not result.answered
    assert "não cobre" in format_result(result)


def test_prompt_numerado_e_flags_sem_ferramentas():
    fake = FakeClaude()
    hits = [_hit(i) for i in (1, 2, 3)]
    answer_question("o que é?", hits, model="sonnet", min_score=0.5, runner=fake)
    argv, stdin = fake.calls[0]
    assert argv[:2] == ["claude", "-p"]
    assert argv[argv.index("--tools") + 1] == ""
    assert "--no-session-persistence" in argv and argv[argv.index("--model") + 1] == "sonnet"
    assert "citar" in argv[argv.index("--system-prompt") + 1] or "cite" in argv[argv.index("--system-prompt") + 1]
    for i in (1, 2, 3):
        assert f"[{i}] Título {i}" in stdin
    assert stdin.rstrip().endswith("Pergunta: o que é?")


def test_fontes_listam_so_os_numeros_citados():
    hits = [_hit(i) for i in (1, 2, 3)]
    result = answer_question("q", hits, model="sonnet", min_score=0.5, runner=FakeClaude())
    out = format_result(result)
    assert "[1] Título 1" in out and "[3] Título 3" in out and "[2] Título 2" not in out


def test_citacoes_agrupadas_e_invalidas():
    assert cited_numbers("a [1][2] b [2, 4] c [9]", 6) == ([1, 2, 4], [9])
    result = answer_question("q", [_hit(1)], model="m", min_score=0.5, runner=FakeClaude("x [1] y [7]"))
    assert "inexistentes ignoradas: 7" in format_result(result)


def test_resposta_sem_citacao_gera_aviso():
    result = answer_question("q", [_hit(1)], model="m", min_score=0.5, runner=FakeClaude("sem fontes"))
    assert result.answered and "sem citações" in format_result(result)


def test_link_do_youtube_com_tempo():
    result = answer_question("q", [_hit(1, kind="youtube", start_s=95)], model="m", min_score=0.5, runner=FakeClaude("a [1]"))
    assert "watch?v=abc&t=95s" in format_result(result)


def test_falha_do_claude_devolve_trechos():
    def broken(argv, stdin):
        raise AskError("limite da assinatura atingido")

    hits = [_hit(1)]
    with pytest.raises(AskError) as exc:
        answer_question("q", hits, model="m", min_score=0.5, runner=broken)
    assert exc.value.hits == hits


def test_historico_em_jsonl(tmp_path):
    result = answer_question("q", [_hit(1)], model="m", min_score=0.5, runner=FakeClaude("a [1]"))
    path = tmp_path / "h.jsonl"
    append_history(path, result)
    append_history(path, result)
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(lines) == 2 and lines[0]["chunks"][0]["doc_id"] == "doc1" and lines[0]["answered"]


def test_eval_grava_relatorio(tmp_path):
    answers = iter(["a [1]", "sem citação", "b [1]"])

    def ask_fn(q):
        return answer_question(q, [_hit(1)], model="m", min_score=0.5, runner=FakeClaude(next(answers)))

    path, cited, total = run_eval(["q1", "q2", "q3"], ask_fn, tmp_path)
    assert (cited, total) == (2, 3)
    text = path.read_text()
    assert text.count("- [ ] As citações sustentam a resposta") == 3 and "2/3 (67%)" in text


def test_cli_ask_help_e_padroes():
    args = build_parser().parse_args(["ask", "o", "que", "é"])
    assert (args.k, args.model, args.min_score) == (6, "sonnet", 0.45)
    assert claude_argv("opus")[claude_argv("opus").index("--model") + 1] == "opus"


def test_prompt_inclui_tier_e_url():
    assert "tier: imprensa | https://x.io/1" in build_prompt("q", [_hit(1, tier="imprensa")])
