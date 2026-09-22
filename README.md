# jev-study

Acervo local e RAG leve para estudar o **Jev**, o modelo "System One" da TypeSafe AI. As fontes curadas (documentação oficial, blog, vídeo do CEO, podcast, integrações e imprensa) são coletadas uma vez; as perguntas são respondidas a partir desse acervo, com citações, sem nova busca na web.

## Requisitos

- [`uv`](https://docs.astral.sh/uv/)
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) (legendas do YouTube)
- [Ollama](https://ollama.com) rodando, com `ollama pull bge-m3`
- Claude Code CLI logado na assinatura (`claude`); nenhuma chave de API é usada

## Uso

```sh
uv sync
uv run jev collect            # coleta sources.toml → data/raw/ (Internet Archive como alternativa)
uv run jev index              # fragmenta e gera embeddings locais → data/index.db
uv run jev ask "o que é um modelo System One?"
uv run jev search "como o Jev expressa confiança" -k 5   # só recuperação, sem gerar
uv run jev sources            # catálogo, status de coleta e trechos por fonte
uv run jev eval               # roda eval/questions.txt → eval/results-<data>.md
```

Opções úteis de `ask`: `--model opus`, `-k 8`, `--show-context` (mostra os trechos enviados), `--min-score 0.6`.

## Como funciona

1. **Coleta** (`collect`): páginas web viram texto; o índice `llms.txt` da documentação oficial é percorrido (até 80 páginas, preferindo a versão `.md`); vídeos entram pela legenda, com marcações de tempo. Se a origem falhar, busca-se o snapshot no Internet Archive.
2. **Índice** (`index`): trechos de até 1 500 caracteres com sobreposição de 200, embeddings `bge-m3` (multilíngue) via Ollama, com descarte de base64 e links gigantes, SQLite + numpy. Reindexa só o que mudou.
3. **Consulta** (`ask`): recupera os 6 trechos mais próximos, ponderados pela confiabilidade da fonte (`oficial` > `tecnica` > `imprensa` > `divulgacao`). Abaixo do limiar (0,45) recusa sem chamar o modelo; acima, chama `claude -p` **sem ferramentas**, que declara quando os trechos não bastam, e imprime a resposta com `[n]` e a lista das fontes citadas (vídeos com o minuto exato).

## Acrescentar fontes

Edite `sources.toml` (campos `id`, `title`, `url`, `kind`, `tier`) e rode `uv run jev collect && uv run jev index`. Para recoletar uma fonte: `uv run jev collect --only <id> --refresh`.

## Testes

```sh
uv run pytest -q
```

Os testes não usam rede, Ollama nem Claude. O planejamento (PRD, specs SDD, roadmap) está em `_reversa_sdd/` e `_reversa_forward/001-mvp-rag-jev/`.
