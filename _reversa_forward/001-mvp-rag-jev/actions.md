# Actions: MVP do jev-study

> Identificador: `001-mvp-rag-jev` · Data: 2026-09-22 · Fonte: `roadmap.md`

**Resumo:** 20 ações · 11 paralelizáveis `[//]` · maior cadeia: T001 → T004 → T010 → T013 → T016 → T018 (6).

## Fase 1: Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `pyproject.toml` (uv, entrada `jev`, numpy, pytest dev) e `src/jev_study/__init__.py` | — | | `pyproject.toml` | 🟢 | [X] |
| T002 | Criar `data/.gitignore` com `*` | — | [//] | `data/.gitignore` | 🟢 | [X] |
| T003 | Criar `sources.toml` com o catálogo curado inicial (SC RF-09) | — | [//] | `sources.toml` | 🟡 | [X] |

## Fase 2: Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Testes de catálogo, HTML→texto, VTT e documento bruto | T001 | [//] | `tests/test_collect_units.py` | 🟢 | [X] |
| T005 | Testes de coleta com `fetch` simulado (web, llms_txt, archive, idempotência, relatório) | T001 | [//] | `tests/test_collect.py` | 🟢 | [X] |
| T006 | Testes de fragmentação, embed simulado e índice/busca | T001 | [//] | `tests/test_index.py` | 🟢 | [X] |
| T007 | Testes de `ask` com `claude` simulado (limiar, prompt, flags, citações, histórico) | T001 | [//] | `tests/test_ask.py` | 🟢 | [X] |

## Fase 3: Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | `config.py`: caminhos e constantes (tiers, pesos, limites) | T001 | | `src/jev_study/config.py` | 🟢 | [X] |
| T009 | `catalog.py`: leitura e validação de `sources.toml` | T008 | [//] | `src/jev_study/catalog.py` | 🟢 | [X] |
| T010 | `htmltext.py` e `vtt.py`: conversões para texto | T008 | [//] | `src/jev_study/htmltext.py` | 🟡 | [X] |
| T011 | `rawdoc.py`: gravação/leitura de `data/raw/<id>.md` com cabeçalho | T008 | [//] | `src/jev_study/rawdoc.py` | 🟢 | [X] |
| T012 | `fetch.py`: GET com timeout, cortesia por domínio e Internet Archive | T008 | [//] | `src/jev_study/fetch.py` | 🟡 | [X] |
| T013 | `collect.py`: orquestração por `kind`, `yt-dlp`, relatório | T009, T010, T011, T012 | | `src/jev_study/collect.py` | 🟡 | [X] |
| T014 | `chunking.py`: trechos com sobreposição e `start_s` | T008 | [//] | `src/jev_study/chunking.py` | 🟢 | [X] |
| T015 | `embed.py`: cliente Ollama com lotes, prefixos e erros | T008 | [//] | `src/jev_study/embed.py` | 🟢 | [X] |
| T016 | `index.py`: SQLite incremental e `search` ponderada | T011, T014, T015 | | `src/jev_study/index.py` | 🟢 | [X] |
| T017 | `ask.py`: limiar, prompt, `claude -p`, citações, histórico | T016 | | `src/jev_study/ask.py` | 🟡 | [X] |

## Fase 4: Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | `cli.py` com `collect`, `index`, `search`, `ask`, `sources`, `eval` (+ `evaluate.py`) | T013, T016, T017 | | `src/jev_study/cli.py` | 🟢 | [X] |
| T019 | Execução real: `uv sync`, `pytest`, `collect`, `index`, `ask` de fumaça | T018 | | — | 🟡 | [X] |

## Fase 5: Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T020 | `README.md` de uso e `eval/questions.txt` inicial | T018 | [//] | `README.md` | 🟢 | [X] |
