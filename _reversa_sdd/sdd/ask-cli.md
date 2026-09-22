# Spec: Consulta com citações (ask-cli)

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-22
**Reviewers:** N/A

> Selo 🟡 PLANEJADO em todos os itens.

---

## 1. Resumo

🟡 Componente de linha de comando `jev` que recebe uma pergunta em linguagem natural, recupera os trechos mais relevantes do índice local e pede ao Claude, pela assinatura do Claude Code CLI (`claude -p`), uma resposta em português baseada só nesses trechos, com citações numeradas e lista de fontes.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Mesmo com o acervo indexado, ler trechos soltos não responde a pergunta; falta a síntese fundamentada.

**Evidências:**
🟡 A métrica central do PRD é "≥ 80% das respostas com citação que sustenta a afirmação".

**Por que agora:**
🟡 É a interface de valor do produto; fecha a jornada da persona.

---

## 3. Goals (Objetivos)

- [ ] G-01: 🟡 ≥ 80% das perguntas do conjunto de avaliação respondidas com citação que sustenta a afirmação.
- [ ] G-02: 🟡 100% das respostas geradas só a partir do acervo local, sem ferramentas nem acesso à web pelo modelo.
- [ ] G-03: 🟡 Recusa explícita em 100% das perguntas sem base no acervo (pontuação máxima abaixo do limiar).

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Respostas com citação correta | não medida | ≥ 80% | primeira avaliação |
| 🟡 Chamadas ao modelo com ferramentas habilitadas | não se aplica | 0% | contínuo |

---

## 4. Non-Goals (Fora do Escopo)

- NG-01: 🟡 Modo de conversa com memória entre perguntas.
- NG-02: 🟡 Interface web ou TUI.
- NG-03: 🟡 Uso de chave de API da Anthropic ou de outro provedor.
- NG-04: 🟡 Avaliação automática da correção das citações por outro modelo; a conferência é humana, a partir do arquivo gerado.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 estudante-tecnico, no terminal.

**Jornada atual (sem a feature):**
🟡 Busca na web, lê várias páginas e monta a resposta de cabeça, sem registro das fontes.

**Jornada futura (com a feature):**
🟡 1. Executa `jev ask "o que é um modelo System One?"`. 2. Lê a resposta com `[1]`, `[2]`. 3. Abre a URL da fonte citada.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O usuário deve poder executar `jev ask "<pergunta>" [-k N] [--model ALIAS] [--show-context]`, com `k` padrão 6 e modelo padrão `sonnet`. | Must | `jev ask --help` lista as opções e os padrões. |
| RF-02 | 🟡 O sistema deve recuperar os `k` trechos por `search` e, se a maior pontuação for menor que 0,45 (recalibrado com `bge-m3`: o limiar só poupa cota; quem recusa perguntas sem base é o prompt), responder "O acervo não cobre essa pergunta" com os três trechos mais próximos, sem chamar o modelo. | Must | Com índice simulado de pontuação máxima 0,3, o `claude` não é invocado e a mensagem aparece. |
| RF-03 | 🟡 O sistema deve montar um prompt com a pergunta e os trechos numerados `[1]..[k]` (título, tier, URL e texto) e instruções para responder em português, usar só os trechos, citar `[n]` após cada afirmação e declarar quando os trechos não bastam. | Must | Prompt de teste contém todos os trechos numerados e a instrução de citar. |
| RF-04 | 🟡 O sistema deve invocar `claude -p --tools "" --no-session-persistence --output-format text --model <alias> --system-prompt <instruções>` passando o contexto pela entrada padrão, com diretório de trabalho temporário e timeout de 180 s. | Must | Chamada simulada recebe exatamente essas flags e nenhuma variável `ANTHROPIC_API_KEY` é exigida. |
| RF-05 | 🟡 O sistema deve imprimir a resposta seguida de "Fontes:" com apenas os números citados, cada um com título, tier e URL (com `&t=Ns` em vídeos do YouTube). | Must | Resposta que cita `[1]` e `[3]` gera lista com as fontes 1 e 3, sem a 2. |
| RF-06 | 🟡 O sistema deve registrar cada consulta em `data/history.jsonl` (data, pergunta, ids dos trechos, pontuações, modelo, resposta). | Should | Após uma consulta, o arquivo ganha uma linha JSON válida. |
| RF-07 | 🟡 O usuário deve poder executar `jev eval [arquivo]`, que roda as perguntas de `eval/questions.txt` (uma por linha) e grava `eval/results-<data>.md` com resposta, fontes e caixa de marcação para conferência humana, e imprime a proporção de respostas com ao menos uma citação. | Should | Arquivo com 3 perguntas gera relatório com 3 seções e o percentual impresso. |
| RF-08 | 🟡 O usuário deve poder executar `jev sources`, que lista o catálogo com status da última coleta e número de trechos indexados por fonte. | Should | Toda fonte do catálogo aparece uma vez na saída. |

> Prioridades: **Must** (obrigatório no MVP) / **Should** (importante, negociável) / **Could** (desejável)

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O usuário executa `jev ask "Como o Jev expressa confiança?"`.
2. 🟡 O sistema gera o embedding da pergunta e recupera 6 trechos.
3. 🟡 O sistema monta o prompt e chama `claude -p` sem ferramentas.
4. 🟡 O sistema imprime a resposta com citações e a lista de fontes citadas.
5. 🟡 Resultado: consulta registrada em `data/history.jsonl`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Pergunta sem base:**
1. 🟡 A maior pontuação fica abaixo de 0,50.
2. 🟡 O sistema informa que o acervo não cobre a pergunta, mostra os trechos mais próximos e sugere acrescentar fonte em `sources.toml`.

**Fluxo Alternativo B — Inspeção do contexto:**
1. 🟡 Com `--show-context`, o sistema imprime os trechos enviados antes da resposta.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Latência total de `ask` | ≤ 60 s no P95 | dominada pelo `claude -p` |
| RNF-02 | 🟡 Tamanho do contexto | ≤ 12 000 caracteres de trechos | k × 1 500 com k = 6 fica em 9 000 |
| RNF-03 | 🟡 Isolamento | modelo sem ferramentas e sem acesso à web | exigência do PRD |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 comandos `jev ask`, `jev eval`, `jev sources`; arquivos `data/history.jsonl` e `eval/`.

**Comportamento esperado:**
🟡 Resposta em texto corrido com `[n]`, linha em branco, bloco "Fontes:".

**Estados da UI:**
- Estado vazio: 🟡 índice vazio imprime "Índice vazio: rode jev collect e jev index", código 0.
- Estado de carregamento: 🟡 linha "consultando o acervo..." e "gerando resposta com <modelo>...".
- Estado de erro: 🟡 mensagem com causa e correção (seção 11).
- Estado de sucesso: 🟡 resposta e fontes.

---

## 9. Modelo de Dados

```
HistoryEntry {
  at: str               // ISO 8601
  question: str
  model: str
  chunks: [{id: int, doc_id: str, score: float}]
  answered: bool        // false quando abaixo do limiar
  answer: str
}
```

**Migrações necessárias:** Não.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 Claude Code CLI (`claude`) autenticado na assinatura | Obrigatória para `ask` | erro com "rode `claude` e faça login"; `jev search` continua disponível |
| 🟡 `knowledge-index.search` | Obrigatória | ver spec knowledge-index |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: 🟡 `claude` ausente no PATH | `FileNotFoundError` | mensagem "Claude Code CLI não encontrado", código 1 |
| EC-02: 🟡 Timeout ou falha do `claude -p` | mais de 180 s ou código de saída diferente de 0 | mostrar stderr resumido e os trechos recuperados como fallback, código 1 |
| EC-03: 🟡 Limite de uso da assinatura atingido | stderr do `claude` menciona limite | mensagem "limite da assinatura atingido; tente mais tarde" e trechos como fallback, código 1 |
| EC-04: 🟡 Resposta sem nenhuma citação | nenhum `[n]` válido no texto | imprimir a resposta com aviso "resposta sem citações: confira nas fontes" e registrar `answered = true` |
| EC-05: 🟡 Citação inexistente | `[n]` com n > k | ignorar o número na lista de fontes e emitir aviso |
| EC-06: 🟡 Pergunta vazia | argumento vazio ou só espaços | erro de uso, código 2 |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 delegada ao Claude Code CLI (login da assinatura).
- **Autorização:** 🟡 modelo invocado com `--tools ""`: não executa comandos nem acessa a web.
- **Dados sensíveis:** 🟡 perguntas e trechos públicos vão para a Anthropic via assinatura; nenhum dado pessoal é enviado.
- **Auditoria:** 🟡 `data/history.jsonl`.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 uso local imediato.
- **Como reverter (rollback):** 🟡 não se aplica; ferramenta pessoal.
- **Monitoramento pós-deploy:** 🟡 rodar `jev eval` com o conjunto inicial e conferir as citações.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 RESOLVIDO em 2026-09-22: com `bge-m3` e índice sem ruído, fora do tema 0,30–0,48 e perguntas genéricas do tema ≈ 0,50; limiar 0,45, recusa fina delegada ao prompt (verificado: "fotossíntese" recusada pelo modelo). Pergunta original: o limiar 0,50 separa bem perguntas cobertas das não cobertas? Premissa: 0,50, ajustável por `--min-score`. | Médio | iago | primeira avaliação |
| OQ-02 | 🟡 ⚠️ ABERTO: o `CLAUDE.md` global do usuário é carregado pelo `claude -p`? Premissa: sim; o prompt de sistema explícito prevalece. | Baixo | iago | primeiro uso |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 Geração via `claude -p` | API da Anthropic, LLM local no Ollama | pedido explícito do usuário: usar a assinatura do Claude Code CLI |
| 🟡 `--tools ""` | ferramentas padrão | garante resposta só com o acervo, sem nova busca na web |
| 🟡 Recusa abaixo do limiar sem chamar o modelo | sempre chamar o modelo | economiza cota e evita alucinação |

---

## Apêndice

### Referências
- 🟡 `_reversa_sdd/prd.md`; `_reversa_sdd/sdd/knowledge-index.md`.

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|--------|------|-------|---------|
| 1.0 | 2026-09-22 | reversa-spec-sdd | Criação inicial |

---

## Relatório de avaliação

- **Score:** 93.0/100 (scripts/spec_scorer.py), 1 iteração.
- **Gaps apontados:** "placeholder não preenchido" é falso positivo: a regex do scorer (`\[[A-Z]...\]` com IGNORECASE) casa com sintaxe legítima da spec (`[[source]]` do TOML, marcação `[t=N]`, argumento opcional `[arquivo]`). Mantido por fidelidade ao formato real.
- **Sugestões:** recalibrar os valores marcados ⚠️ ABERTO após a primeira coleta e avaliação.
