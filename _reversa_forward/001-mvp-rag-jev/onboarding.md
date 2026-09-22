# Onboarding: testar o MVP do jev-study

1. Pré-requisitos: `uv`, `yt-dlp`, Ollama rodando com `bge-m3` (`ollama pull bge-m3`) e Claude Code CLI logado (`claude`).
2. Na raiz do projeto: `uv sync`.
3. Testes automatizados: `uv run pytest -q`.
4. Revisar `sources.toml` e acrescentar ou remover fontes.
5. Coletar: `uv run jev collect`. Conferir a tabela e `data/collect-report.json`.
6. Indexar: `uv run jev index`.
7. Buscar sem gerar: `uv run jev search "como o Jev expressa confiança"`.
8. Perguntar: `uv run jev ask "o que é um modelo System One?"`.
9. Pergunta fora do tema (deve recusar): `uv run jev ask "qual a capital da Mongólia?"`.
10. Avaliar: `uv run jev eval` e revisar `eval/results-<data>.md`, marcando as citações corretas.
