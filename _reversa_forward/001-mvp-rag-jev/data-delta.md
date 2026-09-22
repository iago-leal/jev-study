# Data delta: MVP do jev-study

> Greenfield: não há modelo extraído anterior. Tudo abaixo é novo.

| Artefato | Tipo | Definido em |
|----------|------|-------------|
| `sources.toml` | catálogo versionado | `sdd/source-collection.md#9` (Source) |
| `data/raw/<id>.md` | documento bruto com cabeçalho | `sdd/source-collection.md#9` (Document) |
| `data/collect-report.json` | relatório da última coleta | `sdd/source-collection.md` RF-08 |
| `data/index.db` | SQLite: `documents`, `chunks`, `meta` | `sdd/knowledge-index.md#9` |
| `data/history.jsonl` | histórico de consultas | `sdd/ask-cli.md#9` |
| `eval/questions.txt` | perguntas de avaliação | `sdd/ask-cli.md` RF-07 |
| `eval/results-<data>.md` | resultado para conferência humana | `sdd/ask-cli.md` RF-07 |

`data/` fica fora do git por um `data/.gitignore` próprio com `*` (sem tocar no `.gitignore` da raiz). Ids de `llms_txt` com `/` viram subpastas em `data/raw/<source-id>/<slug>.md`.

Migrações: nenhuma. Mudança do modelo de embedding exige `jev index --rebuild`.
