# Requirements: MVP do jev-study (coleta, índice e consulta com citações)

> Identificador: `001-mvp-rag-jev`
> Data: `2026-09-22`
> Pasta da extração reversa: `_reversa_sdd/` (cenário greenfield: âncora em `prd.md` + `sdd/*.md`)
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Entrega a CLI `jev`, de uso local e pessoal, que coleta um catálogo curado de fontes sobre o Jev (TypeSafe AI), indexa o texto com embeddings locais e responde perguntas em português com citações, gerando a resposta pela assinatura do Claude Code CLI, sem nova busca na web. Projeto novo: não há legado a alterar. 🟡

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/prd.md#4-escopo-in` | coleta web, `llms.txt`, YouTube, Internet Archive; índice local; consulta com citações | 🟡 |
| `_reversa_sdd/prd.md#6-restrições` | Python + `uv`, Ollama `nomic-embed-text`, SQLite, `claude -p` | 🟡 |
| `_reversa_sdd/sdd/source-collection.md#6-requisitos-funcionais` | RF-01..RF-09 da coleta | 🟡 |
| `_reversa_sdd/sdd/knowledge-index.md#6-requisitos-funcionais` | RF-01..RF-08 do índice | 🟡 |
| `_reversa_sdd/sdd/ask-cli.md#6-requisitos-funcionais` | RF-01..RF-08 da consulta | 🟡 |
| `_reversa_sdd/personas.md#persona-1-estudante-tecnico` | jornada de 7 passos no terminal | 🟡 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| estudante-tecnico | entender o Jev com base em fontes verificáveis | pergunta no terminal e recebe resposta com `[n]` e URLs |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** toda resposta gerada cita os trechos numerados que a sustentam; a lista "Fontes:" contém só os números citados. 🟡
   - Tipo: nova
2. **RN-02:** o modelo gerador roda sem ferramentas (`--tools ""`); a resposta depende exclusivamente do acervo local. 🟡
   - Tipo: nova
3. **RN-03:** pergunta cuja maior pontuação de recuperação fica abaixo de 0,50 recebe recusa explícita, sem chamar o modelo. 🟡
   - Tipo: nova
4. **RN-04:** pontuação de recuperação = cosseno × peso do tier (`oficial` 1,00; `tecnica` 0,97; `imprensa` 0,93; `divulgacao` 0,88). 🟡
   - Tipo: nova
5. **RN-05:** falha na origem de uma página web aciona o Internet Archive antes de marcar a fonte como `falhou`; vídeo sem legenda falha direto. 🟡
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Validar e ler `sources.toml` (SC RF-01) | Must | catálogo inválido → código 2, nada coletado | 🟡 |
| RF-02 | Coletar `web` com HTML→texto (SC RF-02) | Must | teste de conversão sem `<script>` e com títulos `#` | 🟡 |
| RF-03 | Coletar `llms_txt` até 80 páginas do mesmo domínio (SC RF-03) | Must | índice de teste com 3 internos e 1 externo → 3 documentos | 🟡 |
| RF-04 | Coletar legenda do YouTube via `yt-dlp` com `[t=N]` (SC RF-04) | Must | VTT de teste sem duplicatas | 🟡 |
| RF-05 | Recorrer ao Internet Archive (SC RF-05) | Must | origem simulada fora do ar → `via = archive` | 🟡 |
| RF-06 | Gravar `data/raw/<id>.md` com cabeçalho e idempotência, `--refresh`, `--only` (SC RF-06, RF-07) | Must | ida e volta do arquivo; segunda execução sem rede | 🟡 |
| RF-07 | Relatório `data/collect-report.json` e tabela (SC RF-08) | Must | cada fonte aparece uma vez | 🟡 |
| RF-08 | Catálogo inicial curado (SC RF-09) | Should | docs oficiais, blog de lançamento e entrevista do CEO presentes | 🟡 |
| RF-09 | Fragmentar em trechos ≤ 1 500 caracteres, sobreposição 200, com `start_s` em vídeos (KI RF-01, RF-02) | Must | testes de fragmentação | 🟡 |
| RF-10 | Embeddings via Ollama com prefixos nomic e lotes ≤ 32 (KI RF-03) | Must | requisição simulada | 🟡 |
| RF-11 | Índice SQLite incremental por `sha256`, `--rebuild` (KI RF-04, RF-05, RF-08) | Must | segunda execução não chama o Ollama | 🟡 |
| RF-12 | `search` ponderada por tier e comando `jev search` (KI RF-06, RF-07) | Must | ordenação por tier em empate | 🟡 |
| RF-13 | `jev ask` com limiar, prompt numerado e `claude -p` sem ferramentas (ASK RF-01..RF-05) | Must | testes com `claude` simulado | 🟡 |
| RF-14 | Histórico em `data/history.jsonl` (ASK RF-06) | Should | uma linha JSON por consulta | 🟡 |
| RF-15 | `jev eval` e `jev sources` (ASK RF-07, RF-08) | Should | relatório de avaliação gerado | 🟡 |

Legenda: SC = `sdd/source-collection.md`; KI = `sdd/knowledge-index.md`; ASK = `sdd/ask-cli.md`.

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | busca ≤ 2 s para 5 000 trechos; `ask` ≤ 60 s no P95 | KI RNF-01; ASK RNF-01 | 🟡 |
| Segurança | modelo sem ferramentas; nenhuma chave de API | ASK RNF-03; PRD §5 | 🟡 |
| Dependências | biblioteca padrão + numpy; `yt-dlp`, Ollama e `claude` externos | SC RNF-03; KI RNF-02 | 🟡 |
| Observabilidade | relatório de coleta e histórico de consultas | SC RF-08; ASK RF-06 | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: coleta do catálogo
  Dado um sources.toml válido
  Quando o usuário executa jev collect
  Então data/raw/ contém um arquivo por documento coletado
  E data/collect-report.json lista todas as fontes com status

Cenário: origem fora do ar
  Dado uma fonte web cuja origem devolve erro 503
  Quando a coleta roda
  Então o sistema consulta o Internet Archive e grava via = archive, ou marca falhou com o motivo

Cenário: pergunta coberta
  Dado o índice construído
  Quando o usuário executa jev ask "o que é um modelo System One?"
  Então a resposta contém ao menos uma citação [n]
  E o bloco Fontes lista título, tier e URL de cada número citado

Cenário: pergunta sem base
  Dado o índice construído
  Quando a maior pontuação fica abaixo de 0,50
  Então o sistema responde que o acervo não cobre a pergunta sem invocar o claude

Cenário: Ollama fora do ar
  Dado o Ollama parado
  Quando o usuário executa jev index
  Então o sistema sai com código 1 e instrução de iniciar o Ollama
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01..RF-07, RF-09..RF-13 | Must | formam a jornada mínima coletar → indexar → perguntar |
| RF-08 | Should | acelera o primeiro uso; o usuário pode editar o catálogo |
| RF-14, RF-15 | Should | medem a métrica de 80% do PRD |
| RNF de desempenho | Should | acervo pequeno; folga ampla |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada. No modo expresso o `/reversa-clarify` é pulado; as dúvidas remanescentes viram premissas 🟡 no `roadmap.md`.

## 10. Lacunas

- 🔴 [DÚVIDA] O limiar 0,50 e os pesos por tier separam bem perguntas cobertas das não cobertas? (ASK OQ-01, KI OQ-01)
- 🔴 [DÚVIDA] Quais vídeos do catálogo têm legenda extraível? (SC OQ-02)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-09-22 | Versão inicial gerada por `/reversa-requirements` (modo expresso) | reversa |
