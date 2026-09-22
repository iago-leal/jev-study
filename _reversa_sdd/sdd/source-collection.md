# Spec: Coleta de fontes (source-collection)

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-22
**Reviewers:** N/A

> Selo 🟡 PLANEJADO em todos os itens.

---

## 1. Resumo

🟡 Componente que lê um catálogo curado de fontes sobre o Jev (TypeSafe AI) e grava no disco o texto de cada uma: páginas web, documentação oficial indexada por `/llms.txt` e transcrições de vídeos do YouTube. Quando a página original falha, recorre ao Internet Archive. Produz um relatório de coleta.

---

## 2. Contexto e Motivação

**Problema:**
🟡 O material sobre o Jev está disperso em documentação, blog, podcast, vídeos e imprensa. Sem uma cópia local, cada pergunta exige nova busca na web.

**Evidências:**
🟡 A TypeSafe lançou o Jev sem artigo técnico nem pesos abertos; a documentação oficial (docs.typesafe.ai) expõe índice em `/llms.txt`; o CEO explicou o modelo em podcast (Latent Space) e em vídeo no YouTube.

**Por que agora:**
🟡 O lançamento ocorreu em setembro de 2026, e o volume de texto de divulgação cresce em ritmo maior que o de fontes primárias.

---

## 3. Goals (Objetivos)

- [ ] G-01: 🟡 Coletar ≥ 90% das fontes do catálogo, contando o Internet Archive como alternativa.
- [ ] G-02: 🟡 Registrar 100% das falhas com motivo legível no relatório.
- [ ] G-03: 🟡 Reexecutar a coleta sem baixar de novo o que já existe (idempotência), salvo com `--refresh`.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Fontes coletadas | 0% | ≥ 90% | primeira coleta |
| 🟡 Falhas com motivo registrado | 0% | 100% | primeira coleta |

---

## 4. Non-Goals (Fora do Escopo)

- NG-01: 🟡 Descobrir fontes novas por busca automática na web; o catálogo é editado à mão.
- NG-02: 🟡 Baixar áudio ou vídeo, ou transcrever áudio localmente quando o vídeo não tem legenda.
- NG-03: 🟡 Renderizar JavaScript (páginas que só exibem conteúdo via JS recorrem ao Internet Archive ou falham com motivo).
- NG-04: 🟡 Seguir links além do índice `/llms.txt` (sem rastreamento recursivo de sites).

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 estudante-tecnico (ver `personas.md`), usuário único, no terminal do Mac.

**Jornada atual (sem a feature):**
🟡 1. Busca "Jev TypeSafe" na web. 2. Abre dezenas de abas. 3. Lê e esquece onde viu cada informação.

**Jornada futura (com a feature):**
🟡 1. Revisa `sources.toml`. 2. Executa `jev collect`. 3. Lê o relatório. 4. Segue para a indexação.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve ler o catálogo `sources.toml`, em que cada entrada `[[source]]` tem `id` (kebab-case, único), `title`, `url`, `kind` (`web`, `youtube` ou `llms_txt`) e `tier` (`oficial`, `tecnica`, `imprensa` ou `divulgacao`), com `notes` opcional. | Must | Catálogo com `id` duplicado, `kind` ou `tier` fora da lista gera erro com o número da entrada e código de saída 2, sem coletar nada. |
| RF-02 | 🟡 O sistema deve, para `kind = web`, baixar a página (timeout 30 s, User-Agent identificado), converter HTML em texto preservando títulos e parágrafos e descartando `script`, `style`, `nav`, `footer` e `header`. | Must | Página HTML de teste gera texto sem conteúdo de `<script>` e com os títulos `h1`–`h3` prefixados por `#`. |
| RF-03 | 🟡 O sistema deve, para `kind = llms_txt`, baixar o índice, extrair os links Markdown do mesmo domínio e coletar cada página listada, até 80 páginas, preferindo a versão `.md` da página quando o servidor a oferece. | Must | Índice de teste com 3 links do domínio e 1 externo gera 3 documentos com `id` `<source-id>/<slug>`. |
| RF-04 | 🟡 O sistema deve, para `kind = youtube`, obter título e legenda via `yt-dlp` sem baixar o vídeo, preferindo legenda manual à automática e inglês ou português, e converter o VTT em texto sem linhas repetidas, mantendo o segundo de início de cada trecho. | Must | VTT de teste com linhas duplicadas de legenda automática gera texto sem duplicatas e marcações `[t=SEGUNDOS]`. |
| RF-05 | 🟡 O sistema deve, quando a coleta original falhar (erro HTTP, timeout ou texto com menos de 200 caracteres), consultar a API de disponibilidade do Internet Archive e coletar o snapshot mais recente na forma bruta (`id_`). | Must | Com a origem simulada fora do ar e snapshot disponível, o documento é gravado com `via = archive`. |
| RF-06 | 🟡 O sistema deve gravar cada documento em `data/raw/<id>.md` com cabeçalho YAML (`id`, `source_id`, `title`, `url`, `tier`, `kind`, `via`, `fetched_at`, `sha256`) seguido do texto. | Must | Arquivo gravado é relido e reproduz os mesmos campos e o mesmo texto. |
| RF-07 | 🟡 O sistema deve pular documentos já gravados, salvo quando o usuário passar `--refresh`; `--only <id>` restringe a coleta a uma fonte. | Must | Segunda execução sem `--refresh` não faz requisições de rede para fontes já gravadas. |
| RF-08 | 🟡 O sistema deve gravar `data/collect-report.json` e imprimir tabela com fonte, status (`ok`, `archive`, `falhou`, `pulado`), número de documentos e motivo da falha. | Must | Toda fonte do catálogo aparece exatamente uma vez no relatório. |
| RF-09 | 🟡 O sistema deve fornecer um catálogo inicial com fontes primárias e técnicas sobre o Jev. | Should | `sources.toml` inicial contém pelo menos a documentação oficial, o blog de lançamento e uma entrevista do CEO. |

> Prioridades: **Must** (obrigatório no MVP) / **Should** (importante, negociável) / **Could** (desejável)

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O usuário executa `jev collect`.
2. 🟡 O sistema valida `sources.toml`.
3. 🟡 O sistema coleta cada fonte conforme o `kind`, gravando os documentos em `data/raw/`.
4. 🟡 O sistema grava o relatório e imprime a tabela de status.
5. 🟡 Resultado: acervo bruto pronto para `jev index`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Origem indisponível:**
1. 🟡 A requisição original falha ou devolve texto curto.
2. 🟡 O sistema tenta o Internet Archive; havendo snapshot, grava com `via = archive`; sem snapshot, marca `falhou` com o motivo.

**Fluxo Alternativo B — Recoleta de uma fonte:**
1. 🟡 O usuário executa `jev collect --only latent-space-jev --refresh`.
2. 🟡 O sistema recoleta só essa fonte e atualiza o relatório.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Tempo por página web | ≤ 30 s de timeout por requisição | evita travar a coleta |
| RNF-02 | 🟡 Cortesia com servidores | 1 requisição por vez, intervalo ≥ 0,5 s no mesmo domínio | coleta pessoal |
| RNF-03 | 🟡 Dependências | só biblioteca padrão do Python mais `yt-dlp` externo | leveza |
| RNF-04 | 🟡 Codificação | UTF-8 sem BOM em todos os arquivos gravados | portabilidade |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 comando `jev collect`, arquivo `sources.toml`, pasta `data/raw/`, arquivo `data/collect-report.json`.

**Comportamento esperado:**
🟡 Uma linha de progresso por fonte (`[3/12] latent-space-jev ... ok`) e, ao final, a tabela-resumo.

**Estados da UI:**
- Estado vazio: 🟡 catálogo sem entradas imprime "Catálogo vazio: edite sources.toml" e sai com código 0.
- Estado de carregamento: 🟡 linha de progresso por fonte.
- Estado de erro: 🟡 falhas por fonte aparecem na tabela; só erro de catálogo ou de disco interrompe a execução.
- Estado de sucesso: 🟡 tabela com contagens de `ok`, `archive`, `falhou` e `pulado`.

---

## 9. Modelo de Dados

```
Source {
  id: str          // kebab-case, único
  title: str
  url: str
  kind: "web" | "youtube" | "llms_txt"
  tier: "oficial" | "tecnica" | "imprensa" | "divulgacao"
  notes: str?
}

Document {
  id: str          // igual a source.id, ou "<source.id>/<slug>" para llms_txt
  source_id: str
  title: str
  url: str
  tier: str
  kind: str
  via: "original" | "archive"
  fetched_at: str  // ISO 8601
  sha256: str      // do texto
  text: str
}
```

**Migrações necessárias:** Não.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 Sites das fontes | Obrigatória | fallback para o Internet Archive |
| 🟡 API do Internet Archive (`archive.org/wayback/available`) | Opcional | fonte marcada `falhou` com motivo |
| 🟡 `yt-dlp` no PATH | Obrigatória para `youtube` | fontes `youtube` marcadas `falhou` com "yt-dlp não encontrado" |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: 🟡 Timeout ou erro 4xx/5xx | origem não responde em 30 s ou devolve erro HTTP | tentar o Internet Archive; sem snapshot, `falhou` com código HTTP ou "timeout" |
| EC-02: 🟡 Vídeo sem legenda | `yt-dlp` não encontra legenda em inglês ou português | `falhou` com "sem legenda disponível"; não tenta o Internet Archive |
| EC-03: 🟡 Catálogo inválido | TOML malformado, campo obrigatório ausente, `id` duplicado | erro com a entrada problemática, código de saída 2, nada é coletado |
| EC-04: 🟡 Página renderizada por JS | texto extraído com menos de 200 caracteres | tratar como falha de origem e tentar o Internet Archive |
| EC-05: 🟡 `llms_txt` com mais de 80 links | índice extenso | coletar os 80 primeiros e registrar aviso no relatório |
| EC-06: 🟡 Disco sem permissão de escrita | falha ao gravar em `data/` | interromper com mensagem indicando o caminho, código de saída 1 |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 não se aplica; uso local de um único usuário.
- **Autorização:** 🟡 não se aplica.
- **Dados sensíveis:** 🟡 nenhum; apenas conteúdo público.
- **Auditoria:** 🟡 o relatório de coleta registra data, origem e via de cada documento.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 uso local imediato; sem implantação.
- **Como reverter (rollback):** 🟡 apagar `data/raw/` e recoletar.
- **Monitoramento pós-deploy:** 🟡 revisar o relatório da primeira coleta.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 ⚠️ ABERTO: a documentação oficial oferece versão `.md` das páginas? Premissa: tentar `.md` e recorrer ao HTML. | Baixo | iago | primeira coleta |
| OQ-02 | 🟡 ⚠️ ABERTO: quais vídeos do YouTube têm legenda? Premissa: o relatório revela. | Médio | iago | primeira coleta |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 Conversão HTML→texto com `html.parser` da biblioteca padrão | trafilatura, BeautifulSoup | zero dependências; fontes são poucas e conhecidas |
| 🟡 Legendas via `yt-dlp` | youtube-transcript-api | já instalado no Mac do usuário e mantido ativamente |
| 🟡 Internet Archive como alternativa | só a origem | o usuário citou o "archive" no brief |

---

## Apêndice

### Referências
- 🟡 `_reversa_sdd/prd.md`, seções 4 e 8.
- 🟡 https://docs.typesafe.ai/llms.txt

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|--------|------|-------|---------|
| 1.0 | 2026-09-22 | reversa-spec-sdd | Criação inicial |

---

## Relatório de avaliação

- **Score:** 91.0/100 (scripts/spec_scorer.py), 1 iteração.
- **Gaps apontados:** "placeholder não preenchido" é falso positivo: a regex do scorer (`\[[A-Z]...\]` com IGNORECASE) casa com sintaxe legítima da spec (`[[source]]` do TOML, marcação `[t=N]`, argumento opcional `[arquivo]`). Mantido por fidelidade ao formato real.
- **Sugestões:** recalibrar os valores marcados ⚠️ ABERTO após a primeira coleta e avaliação.
