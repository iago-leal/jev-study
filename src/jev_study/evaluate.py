"""Avaliação por conjunto de perguntas, com conferência humana (ask-cli RF-07)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable

from .ask import AskError, AskResult


def load_questions(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [q.strip() for q in lines if q.strip() and not q.lstrip().startswith("#")]


def run_eval(questions: list[str], ask_fn: Callable[[str], AskResult], out_dir: Path) -> tuple[Path, int, int]:
    """Grava eval/results-<data>.md e devolve (caminho, respostas com citação, total)."""
    sections: list[str] = []
    with_citation = 0
    for n, question in enumerate(questions, start=1):
        try:
            result = ask_fn(question)
            body, sources = result.answer, [
                f"- [{c}] {result.hits[c - 1].title} ({result.hits[c - 1].tier}) {result.hits[c - 1].cite_url}"
                for c in result.cited
            ]
            status = "respondida" if result.answered else "recusada (abaixo do limiar)"
            with_citation += bool(result.cited)
        except AskError as exc:
            body, sources, status = f"Erro: {exc}", [], "erro"
        sections.append(
            f"## {n}. {question}\n\n**Status:** {status}\n\n{body}\n\n"
            + ("**Fontes citadas:**\n" + "\n".join(sources) + "\n\n" if sources else "")
            + "- [ ] As citações sustentam a resposta\n"
        )
    total = len(questions)
    pct = 100 * with_citation / total if total else 0.0
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"results-{date.today().isoformat()}.md"
    header = (
        f"# Avaliação do jev-study ({date.today().isoformat()})\n\n"
        f"Respostas com ao menos uma citação: {with_citation}/{total} ({pct:.0f}%).\n"
        "Meta do PRD: ≥ 80% com citação que de fato sustenta a resposta. Marque abaixo as corretas.\n\n"
    )
    path.write_text(header + "\n".join(sections), encoding="utf-8")
    return path, with_citation, total
