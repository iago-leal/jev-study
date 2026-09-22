# Roadmap: MVP do jev-study

> Identificador: `001-mvp-rag-jev` · Data: 2026-09-22 · Cenário greenfield (âncora `_reversa_sdd/prd.md` + `sdd/*.md`)

## 1. Resumo da abordagem

Pacote Python `jev_study` (layout `src/`, gerido por `uv`) com uma CLI `jev` de cinco subcomandos: `collect`, `index`, `search`, `ask`, `sources` e `eval`. A coleta usa só a biblioteca padrão (`urllib`, `html.parser`, `tomllib`) e o `yt-dlp` externo; o índice usa SQLite e numpy; os embeddings vêm do Ollama local; a resposta vem de `claude -p` sem ferramentas. Dependências externas ficam atrás de funções injetáveis, e os testes rodam sem rede, sem Ollama e sem Claude.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Não modificar arquivos pré-existentes | todo código é arquivo novo; `data/.gitignore` novo evita tocar o `.gitignore` da raiz | respeita |
| "RAG bem levinho" (brief) | sem banco vetorial, sem framework de RAG | respeita |

`.reversa/principles.md` não existe; valem os princípios acima, derivados do brief e do `CLAUDE.md` do projeto.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Layout `src/jev_study/`, entrada `jev = "jev_study.cli:main"` | padrão do `uv`; importável nos testes | script único | 🟢 |
| D-02 | CLI com `argparse` | zero dependência | typer, click | 🟢 |
| D-03 | HTML→texto com `html.parser` | zero dependência | trafilatura, bs4 | 🟡 |
| D-04 | Cabeçalho dos documentos brutos em YAML simples (`chave: valor` com valores JSON-escapados), lido por parser próprio | evita PyYAML | PyYAML | 🟡 |
| D-05 | SQLite + numpy com força bruta | acervo < 5 000 trechos | Chroma, sqlite-vec | 🟢 |
| D-06 | Embeddings `nomic-embed-text` via `POST /api/embed` | já instalado localmente | sentence-transformers | 🟢 |
| D-07 | `claude -p --tools "" --no-session-persistence --system-prompt ...` com cwd temporário | assinatura do usuário; isolamento | API Anthropic, Ollama como gerador | 🟡 |
| D-08 | Injeção de dependências (`fetch`, `embed`, `run_claude`) por parâmetro | testes herméticos | mocks globais | 🟢 |
| D-09 | Testes com `pytest` como dependência de desenvolvimento | padrão do ecossistema | unittest | 🟢 |

## 4. Premissas

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| Limiar 0,50 e pesos por tier adequados; ajustáveis por `--min-score` | §10, DÚVIDA 1 | recusas indevidas ou respostas com base fraca |
| O relatório de coleta revela quais vídeos têm legenda | §10, DÚVIDA 2 | vídeos ausentes do acervo |
| `docs.typesafe.ai` serve Markdown ao acrescentar `.md` à URL (padrão Mintlify); senão, HTML | SC OQ-01 | texto com ruído de navegação |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| source-collection | `_reversa_sdd/sdd/source-collection.md` | componente-novo | `catalog.py`, `htmltext.py`, `vtt.py`, `fetch.py`, `rawdoc.py`, `collect.py` |
| knowledge-index | `_reversa_sdd/sdd/knowledge-index.md` | componente-novo | `chunking.py`, `embed.py`, `index.py` |
| ask-cli | `_reversa_sdd/sdd/ask-cli.md` | componente-novo | `ask.py`, `evaluate.py`, `cli.py` |

## 6. Delta no modelo de dados

Ver `data-delta.md`: `data/raw/*.md`, `data/collect-report.json`, `data/index.db`, `data/history.jsonl`.

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Ollama embed | HTTP | `interfaces/ollama-embed.md` |
| Claude Code CLI | processo | `interfaces/claude-cli.md` |
| Internet Archive availability | HTTP | `interfaces/wayback.md` |

## 8. Plano de migração

Não se aplica (greenfield). Instalação: `uv sync`, depois `uv run jev collect && uv run jev index`.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Sites bloqueiam o User-Agent padrão do urllib | médio | média | User-Agent de navegador + identificação; fallback Internet Archive |
| `yt-dlp` desatualizado falha no YouTube | médio | média | mensagem sugerindo `brew upgrade yt-dlp` |
| `claude -p` carrega o `CLAUDE.md` global e altera o estilo | baixo | alta | prompt de sistema explícito; cwd temporário |
| Python 3.14 sem wheel de numpy | médio | baixa | numpy 2.5 já instalado no sistema; `uv` resolve |

## 10. Critério de pronto

- `uv run pytest` verde.
- `uv run jev collect` com o catálogo inicial coleta ≥ 90% das fontes.
- `uv run jev index` indexa todos os documentos.
- `uv run jev ask "o que é um modelo System One?"` devolve resposta com citações.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-09-22 | Versão inicial gerada por `/reversa-plan` (modo expresso) | reversa |
