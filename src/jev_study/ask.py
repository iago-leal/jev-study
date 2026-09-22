"""Consulta com citações via `claude -p` sem ferramentas (ask-cli RF-02..RF-06)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .config import CLAUDE_TIMEOUT_S
from .index import Hit

SYSTEM_PROMPT = """\
Você é um assistente de estudo sobre o Jev, modelo "System One" da TypeSafe AI.
Responda em português do Brasil usando exclusivamente os trechos numerados fornecidos pelo usuário.
Regras:
1. Após cada afirmação, cite entre colchetes o número do trecho que a sustenta, como [1] ou [2][4].
2. Não use conhecimento externo aos trechos nem invente números, datas, nomes ou benchmarks.
3. Se os trechos não bastarem para responder, declare isso explicitamente e diga o que falta.
4. Trechos de tier "imprensa" ou "divulgacao" podem exagerar; havendo conflito com tier "oficial", prefira o oficial e aponte a divergência.
5. Seja direto: sem preâmbulo, sem repetir a pergunta, sem lista de fontes no final (ela é gerada à parte)."""

_CITE_RE = re.compile(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]")

Runner = Callable[[list[str], str], str]  # (argv, stdin) -> stdout


class AskError(Exception):
    def __init__(self, message: str, hits: list[Hit] | None = None, exit_code: int = 1):
        super().__init__(message)
        self.hits = hits or []
        self.exit_code = exit_code


@dataclass
class AskResult:
    question: str
    model: str
    hits: list[Hit]
    answered: bool
    answer: str
    cited: list[int] = field(default_factory=list)
    invalid: list[int] = field(default_factory=list)


def build_prompt(question: str, hits: list[Hit]) -> str:
    blocks = [
        f"[{n}] {h.title} | tier: {h.tier} | {h.cite_url}\n{h.text}"
        for n, h in enumerate(hits, start=1)
    ]
    return "Trechos do acervo:\n\n" + "\n\n".join(blocks) + f"\n\nPergunta: {question}\n"


def claude_argv(model: str, system_prompt: str = SYSTEM_PROMPT) -> list[str]:
    return [
        "claude", "-p",
        "--tools", "",
        "--no-session-persistence",
        "--output-format", "text",
        "--model", model,
        "--system-prompt", system_prompt,
    ]


def run_claude(argv: list[str], stdin: str, timeout: float = CLAUDE_TIMEOUT_S) -> str:
    # Sem ANTHROPIC_API_KEY no ambiente, o CLI usa o login da assinatura, nunca cobrança por API.
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    with tempfile.TemporaryDirectory(prefix="jev-ask-") as cwd:
        try:
            proc = subprocess.run(argv, input=stdin, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env)
        except FileNotFoundError:
            raise AskError("Claude Code CLI não encontrado no PATH; instale-o e rode `claude` para fazer login") from None
        except subprocess.TimeoutExpired:
            raise AskError(f"claude -p excedeu {int(timeout)} s") from None
    if proc.returncode != 0:
        detail = (proc.stderr.strip() or proc.stdout.strip() or f"código {proc.returncode}")[-400:]
        if re.search(r"limit|quota|usage", detail, re.IGNORECASE):
            raise AskError(f"limite da assinatura atingido; tente mais tarde ({detail})")
        if re.search(r"log ?in|auth", detail, re.IGNORECASE):
            raise AskError(f"Claude Code CLI sem login: rode `claude` e faça login ({detail})")
        raise AskError(f"claude -p falhou: {detail}")
    return proc.stdout.strip()


def cited_numbers(answer: str, k: int) -> tuple[list[int], list[int]]:
    nums: set[int] = set()
    for group in _CITE_RE.findall(answer):
        nums.update(int(n) for n in re.split(r"\s*[,;]\s*", group))
    valid = sorted(n for n in nums if 1 <= n <= k)
    invalid = sorted(n for n in nums if not 1 <= n <= k)
    return valid, invalid


def append_history(path: Path, result: AskResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "question": result.question,
        "model": result.model,
        "chunks": [{"id": h.chunk_id, "doc_id": h.doc_id, "score": round(h.score, 4)} for h in result.hits],
        "answered": result.answered,
        "answer": result.answer,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def answer_question(
    question: str,
    hits: list[Hit],
    *,
    model: str,
    min_score: float,
    runner: Runner | None = None,
) -> AskResult:
    if not hits or hits[0].score < min_score:
        return AskResult(question, model, hits[:3], answered=False, answer="O acervo não cobre essa pergunta.")
    runner = runner or run_claude
    try:
        answer = runner(claude_argv(model), build_prompt(question, hits))
    except AskError as exc:
        exc.hits = hits
        raise
    cited, invalid = cited_numbers(answer, len(hits))
    return AskResult(question, model, hits, True, answer, cited, invalid)


def format_result(result: AskResult) -> str:
    if not result.answered:
        lines = [result.answer, "", "Trechos mais próximos (abaixo do limiar):"]
        lines += [f"  {h.score:.2f}  {h.title} [{h.tier}]  {h.cite_url}" for h in result.hits]
        lines += ["", "Se o tema for relevante, acrescente uma fonte em sources.toml e rode jev collect && jev index."]
        return "\n".join(lines)
    lines = [result.answer, ""]
    if not result.cited:
        lines.append("Aviso: resposta sem citações; confira nas fontes antes de confiar nela.")
    if result.invalid:
        lines.append(f"Aviso: citações inexistentes ignoradas: {', '.join(map(str, result.invalid))}")
    if result.cited:
        lines.append("Fontes:")
        for n in result.cited:
            h = result.hits[n - 1]
            lines.append(f"  [{n}] {h.title} ({h.tier}) {h.cite_url}")
    return "\n".join(lines).rstrip()
