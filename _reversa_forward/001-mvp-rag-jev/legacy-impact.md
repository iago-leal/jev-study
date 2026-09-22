# Legacy impact: 001-mvp-rag-jev

> Data: 2026-09-22
> Feature greenfield, sem legado pré-existente. Âncora: prd.md + specs SDD.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (liberação irrestrita). Mesmo assim, só foram criados arquivos novos; nenhum arquivo pré-existente do projeto foi modificado.

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `pyproject.toml`, `uv.lock`, `src/jev_study/__init__.py`, `src/jev_study/config.py` | (transversal) | componente-novo | LOW | empacotamento e constantes |
| `sources.toml` | source-collection | componente-novo | LOW | catálogo curado (SC RF-09) |
| `src/jev_study/catalog.py`, `htmltext.py`, `vtt.py`, `rawdoc.py`, `fetch.py`, `collect.py` | source-collection | componente-novo | LOW | SC RF-01..RF-08 |
| `src/jev_study/chunking.py`, `embed.py`, `index.py` | knowledge-index | componente-novo | LOW | KI RF-01..RF-08 |
| `src/jev_study/ask.py`, `evaluate.py`, `cli.py` | ask-cli | componente-novo | LOW | ASK RF-01..RF-08 |
| `tests/*.py` | os três | componente-novo | LOW | 38 testes herméticos |
| `data/.gitignore` | (transversal) | componente-novo | LOW | mantém o acervo fora do git sem tocar no `.gitignore` da raiz |
| `README.md`, `eval/questions.txt` | ask-cli | componente-novo | LOW | uso e avaliação |

## Diff conceitual por componente

- **source-collection:** coleta com três estratégias (`web`, `llms_txt`, `youtube`) e fallback no Internet Archive. Desvio da spec: o `yt-dlp` é chamado um idioma por vez, porque pedir vários de uma vez provocou HTTP 429 na coleta real.
- **knowledge-index:** conforme a spec. Um trecho sem marcação `[t=N]` herda a última marcação vista, o que complementa a RF-02.
- **knowledge-index (pós-avaliação):** embedding trocado para `bge-m3` (multilíngue) e limpeza de base64/links de playground antes da fragmentação (66 trechos ruidosos eliminados; 1 331 trechos).
- **ask-cli:** conforme a spec, com o limiar recalibrado de 0,50 para 0,58 e, após a troca de embedding, para 0,45 (spec atualizada; OQ-01 resolvida). O `ANTHROPIC_API_KEY` é removido do ambiente do subprocesso para garantir o uso da assinatura.

## Preservadas

Não se aplica (greenfield).

## Modificadas

Não se aplica (greenfield).
