# Spec: Índice de conhecimento (knowledge-index)

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-22
**Reviewers:** N/A

> Selo 🟡 PLANEJADO em todos os itens.

---

## 1. Resumo

🟡 Componente que fragmenta os documentos de `data/raw/`, gera embeddings locais pelo Ollama (`bge-m3`, multilíngue; era `nomic-embed-text`) e os guarda num SQLite. Expõe a busca semântica usada pela consulta, com ajuste pelo nível de confiabilidade da fonte.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Sem índice, cada pergunta exigiria reler todo o acervo ou buscar de novo na web.

**Evidências:**
🟡 O PRD exige respostas sem acesso à web e com citação; a recuperação precisa devolver o trecho e a fonte.

**Por que agora:**
🟡 É o elo entre a coleta e a consulta; sem ele o MVP não responde perguntas.

---

## 3. Goals (Objetivos)

- [ ] G-01: 🟡 Indexar 100% dos documentos de `data/raw/`.
- [ ] G-02: 🟡 Reindexar apenas documentos cujo `sha256` mudou.
- [ ] G-03: 🟡 Responder a uma busca em ≤ 2 s para um acervo de até 5 000 trechos, sem contar o embedding da pergunta.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Documentos indexados | 0% | 100% | primeira indexação |
| 🟡 Latência da busca (5 000 trechos) | não medida | ≤ 2 s | primeira versão |

---

## 4. Non-Goals (Fora do Escopo)

- NG-01: 🟡 Banco vetorial externo (Chroma, pgvector, serviços em nuvem).
- NG-02: 🟡 Busca híbrida com BM25 ou reordenação por modelo cruzado nesta versão.
- NG-03: 🟡 Embeddings por API paga.
- NG-04: 🟡 Índice aproximado (HNSW, IVF); a busca é exata por força bruta.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 estudante-tecnico; também o componente `ask-cli`, que consome a busca.

**Jornada atual (sem a feature):**
🟡 O usuário procura com `grep` nos textos, sem busca por significado.

**Jornada futura (com a feature):**
🟡 1. Executa `jev index`. 2. Executa `jev search "pergunta"` e vê os trechos mais próximos com a fonte.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve fragmentar cada documento em trechos de até 1 500 caracteres com sobreposição de 200, quebrando preferencialmente em limite de parágrafo. | Must | Documento de 4 000 caracteres gera 3 ou 4 trechos, nenhum acima de 1 500 caracteres. |
| RF-02 | 🟡 O sistema deve, em documentos do YouTube, atribuir a cada trecho o segundo de início da primeira marcação `[t=N]` que contém e remover as marcações do texto do trecho. | Must | Trecho com `[t=125]` recebe `start_s = 125` e não contém a marcação. |
| RF-03 | 🟡 O sistema deve gerar embeddings pelo endpoint `POST /api/embed` do Ollama com o modelo `bge-m3` (configurável por `JEV_EMBED_MODEL`), em lotes de até 32 trechos, aplicando os prefixos de tarefa do modelo quando existirem (`search_document: `/`search_query: ` no `nomic-embed-text`; nenhum no `bge-m3`). Antes de fragmentar, o sistema deve descartar data URIs, tokens base64 isolados com 80 ou mais caracteres e payloads de query/fragmento de URL com 80 ou mais caracteres. | Must | Requisição simulada recebe os prefixos corretos e lotes de no máximo 32 itens. |
| RF-04 | 🟡 O sistema deve gravar documentos e trechos em `data/index.db` (SQLite), com o embedding como vetor `float32` normalizado. | Must | Vetor lido do banco tem norma 1 ± 1e-5. |
| RF-05 | 🟡 O sistema deve reindexar só os documentos novos ou com `sha256` diferente e remover do índice documentos ausentes de `data/raw/`; `--rebuild` recria tudo. | Must | Segunda execução sem mudanças não chama o Ollama. |
| RF-06 | 🟡 O sistema deve oferecer a função `search(pergunta, k)` que devolve os `k` trechos de maior pontuação, onde pontuação = similaridade de cosseno × peso do tier (`oficial` 1,00; `tecnica` 0,97; `imprensa` 0,93; `divulgacao` 0,88). | Must | Com dois trechos de mesma similaridade, o de tier `oficial` vem antes do de `divulgacao`. |
| RF-07 | 🟡 O usuário deve poder executar `jev search "<pergunta>" [-k N]` e ver, para cada trecho, pontuação, título, tier, URL (com `&t=Ns` em vídeos) e os primeiros 300 caracteres. | Must | Saída de teste lista `k` trechos em ordem decrescente de pontuação. |
| RF-08 | 🟡 O sistema deve imprimir, ao final de `jev index`, número de documentos novos, atualizados, removidos e total de trechos. | Should | Contagens batem com o conteúdo do banco. |

> Prioridades: **Must** (obrigatório no MVP) / **Should** (importante, negociável) / **Could** (desejável)

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O usuário executa `jev index`.
2. 🟡 O sistema lê `data/raw/*.md` e compara `sha256` com o banco.
3. 🟡 O sistema fragmenta e gera embeddings dos documentos novos ou alterados.
4. 🟡 O sistema grava trechos e remove documentos órfãos.
5. 🟡 Resultado: índice atualizado e resumo impresso.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Reconstrução completa:**
1. 🟡 O usuário executa `jev index --rebuild`.
2. 🟡 O sistema apaga as tabelas e reindexa todos os documentos.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Latência de busca | ≤ 2 s para 5 000 trechos | produto matricial com numpy |
| RNF-02 | 🟡 Dependências | biblioteca padrão + numpy | leveza |
| RNF-03 | 🟡 Operação sem rede externa | 100% local (Ollama em localhost) | exigência do PRD |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 comandos `jev index` e `jev search`; arquivo `data/index.db`.

**Comportamento esperado:**
🟡 `jev index` mostra uma linha por documento processado; `jev search` lista os trechos numerados.

**Estados da UI:**
- Estado vazio: 🟡 sem documentos em `data/raw/`, imprime "Acervo vazio: rode jev collect" e sai com código 0.
- Estado de carregamento: 🟡 linha `indexando <id> (N trechos)`.
- Estado de erro: 🟡 mensagem com a causa e a correção (ver seção 11).
- Estado de sucesso: 🟡 resumo com contagens.

---

## 9. Modelo de Dados

```
documents {
  id TEXT PRIMARY KEY
  source_id TEXT
  title TEXT
  url TEXT
  tier TEXT
  kind TEXT
  sha256 TEXT
  indexed_at TEXT
}

chunks {
  id INTEGER PRIMARY KEY
  doc_id TEXT REFERENCES documents(id) ON DELETE CASCADE
  ord INTEGER        // posição no documento
  text TEXT
  start_s INTEGER    // só YouTube; nulo nos demais
  embedding BLOB     // float32, normalizado
}

meta { key TEXT PRIMARY KEY, value TEXT }  // modelo e dimensão do embedding
```

**Migrações necessárias:** Não (criação inicial).

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 Ollama em `http://localhost:11434` | Obrigatória | erro com instrução "inicie o Ollama" |
| 🟡 Modelo `nomic-embed-text` | Obrigatória | erro com instrução `ollama pull nomic-embed-text` |
| 🟡 numpy | Obrigatória | instalado pelo `uv` |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: 🟡 Ollama fora do ar | conexão recusada ou timeout de 60 s | interromper com "Ollama indisponível em localhost:11434; inicie-o com `ollama serve`", código 1; documentos já gravados permanecem |
| EC-02: 🟡 Modelo ausente | Ollama devolve erro 404 de modelo | interromper com "rode `ollama pull nomic-embed-text`", código 1 |
| EC-03: 🟡 Troca de modelo de embedding | `meta.model` diferente do configurado | exigir `--rebuild` com mensagem explicativa, código 2 |
| EC-04: 🟡 Documento vazio | texto sem conteúdo após o cabeçalho | pular o documento e registrar aviso |
| EC-05: 🟡 Busca com índice vazio | `jev search` sem trechos | imprimir "Índice vazio: rode jev index", código 0 |
| EC-06: 🟡 Arquivo em `data/raw/` com cabeçalho inválido | YAML ausente ou malformado | pular com aviso indicando o arquivo |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 não se aplica.
- **Autorização:** 🟡 não se aplica.
- **Dados sensíveis:** 🟡 nenhum; embeddings gerados localmente.
- **Auditoria:** 🟡 `documents.indexed_at` registra a última indexação.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 uso local imediato.
- **Como reverter (rollback):** 🟡 apagar `data/index.db` e reindexar.
- **Monitoramento pós-deploy:** 🟡 conferir `jev search` com três perguntas de controle.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 ⚠️ ABERTO: os pesos por tier são adequados? Premissa: valores da RF-06, recalibrar após avaliação. | Médio | iago | após a primeira avaliação |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 `bge-m3` no lugar de `nomic-embed-text` (2026-09-22) | manter nomic; traduzir a pergunta com LLM local | avaliação: perguntas em português contra acervo em inglês pontuavam 0,54 no nomic (recusa indevida) e 0,61+ no bge-m3 |
| 🟡 SQLite + numpy, busca exata | Chroma, sqlite-vec, FAISS | acervo pequeno; zero serviço extra; "RAG bem levinho" |
| 🟡 `nomic-embed-text` via Ollama | sentence-transformers, fastembed | já instalado; sem baixar PyTorch |
| 🟡 Peso por tier multiplicativo | filtro rígido por tier | privilegia fonte primária sem descartar imprensa |

---

## Apêndice

### Referências
- 🟡 `_reversa_sdd/prd.md`; `_reversa_sdd/sdd/source-collection.md` (formato de `data/raw/`).

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|--------|------|-------|---------|
| 1.0 | 2026-09-22 | reversa-spec-sdd | Criação inicial |

---

## Relatório de avaliação

- **Score:** 93.0/100 (scripts/spec_scorer.py), 1 iteração.
- **Gaps apontados:** "placeholder não preenchido" é falso positivo: a regex do scorer (`\[[A-Z]...\]` com IGNORECASE) casa com sintaxe legítima da spec (`[[source]]` do TOML, marcação `[t=N]`, argumento opcional `[arquivo]`). Mantido por fidelidade ao formato real.
- **Sugestões:** recalibrar os valores marcados ⚠️ ABERTO após a primeira coleta e avaliação.
