# Regression watch: 001-mvp-rag-jev

> Feature greenfield: não há regras 🟢 extraídas a vigiar. Os RFs abaixo ficam em "Observações" até que um `/reversa` sobre o código novo os confirme.

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem | Regra implementada | Como verificar |
|----|--------|--------------------|----------------|
| W001 | `sdd/ask-cli.md` RF-04 | `claude -p` sempre com `--tools ""` e sem `ANTHROPIC_API_KEY` | `tests/test_ask.py::test_prompt_numerado_e_flags_sem_ferramentas` |
| W002 | `sdd/ask-cli.md` RF-02 | recusa abaixo do limiar (0,58) sem chamar o modelo | `test_abaixo_do_limiar_nao_chama_o_modelo` |
| W003 | `sdd/ask-cli.md` RF-05 | "Fontes:" lista só os números citados | `test_fontes_listam_so_os_numeros_citados` |
| W004 | `sdd/knowledge-index.md` RF-06 | pontuação = cosseno × peso do tier | `test_busca_ordena_por_pontuacao_e_desempata_por_tier` |
| W005 | `sdd/knowledge-index.md` RF-05 | reindexação só do que mudou | `test_indice_incremental_normalizado_e_orfaos` |
| W006 | `sdd/source-collection.md` RF-05 | fallback no Internet Archive | `test_origem_fora_do_ar_recorre_ao_archive` |
| W007 | `sdd/source-collection.md` RF-07 | coleta idempotente | `test_idempotencia_e_refresh` |

## Histórico de re-extrações

(vazio)

## Arquivadas

(vazio)
