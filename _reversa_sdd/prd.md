# PRD: jev-study

> Selo 🟡 PLANEJADO. Documento gerado a partir de ideation + personas.

**Versão:** 1.0
**Data:** 2026-09-22
**Autor:** reversa-drafter
**Status:** rascunho

---

## 1. Problema

🟡 O Jev (TypeSafe AI), primeiro modelo "System One", foi lançado em setembro de 2026 sem artigo técnico nem pesos abertos. O conhecimento sobre ele está espalhado entre documentação oficial, blog, podcasts, vídeos e imprensa, e mistura fonte primária com texto promocional. Estudar o tema exige refazer buscas a cada dúvida.

### Quem sente
🟡 O estudante técnico (persona única), nas sessões de estudo no terminal, sempre que surge uma pergunta sobre o funcionamento, os limites ou a integração do Jev.

---

## 2. Personas-alvo

🟡 Referência completa em [`personas.md`](./personas.md). Resumo:

- **estudante-tecnico**: 🟡 desenvolvedor avançado em Python que estuda IA aplicada; sofre com material disperso e promocional.

---

## 3. Métricas de sucesso

| Métrica | Unidade | Alvo | Prazo |
|---|---|---|---|
| 🟡 Respostas com citação que sustenta a afirmação | % do conjunto de avaliação | ≥ 80% | primeira versão |
| 🟡 Fontes da lista curada coletadas com sucesso | % das fontes | ≥ 90% (contando o Internet Archive como alternativa) | primeira coleta |
| 🟡 Perguntas respondidas sem acesso à web | % das perguntas | 100% | contínuo |

---

## 4. Escopo (in)

- 🟡 Lista curada de fontes em arquivo versionado, com nível de confiabilidade por fonte (oficial, técnica, imprensa, divulgação).
- 🟡 Coleta de páginas web (documentação oficial via `/llms.txt`, blog, artigos) com conversão para texto.
- 🟡 Coleta de transcrições de vídeos do YouTube pelas legendas (manuais ou automáticas).
- 🟡 Alternativa de coleta pelo Internet Archive (Wayback Machine) quando a página original falhar.
- 🟡 Fragmentação do texto, geração de embeddings locais e armazenamento num índice local.
- 🟡 Consulta em linguagem natural pela CLI: recuperação dos trechos mais relevantes e resposta gerada pela assinatura do Claude Code CLI, com citações.
- 🟡 Comando de busca semântica sem geração (só trechos e fontes).
- 🟡 Relatório de coleta (o que entrou, o que falhou e por quê).

---

## 5. Não-objetivos (out)

- 🟡 Interface web elaborada.
- 🟡 Uso multiusuário, autenticação ou implantação em servidor.
- 🟡 Reprodução de vídeo ou download de áudio/vídeo.
- 🟡 Descoberta automática de fontes novas por busca na web (a lista é curada à mão).
- 🟡 Uso da API paga da Anthropic ou de chaves de API.

---

## 6. Restrições

| Tipo | Descrição |
|---|---|
| 🟡 Técnica | 🟡 Python ≥ 3.12 gerido por `uv`; embeddings locais via Ollama (`nomic-embed-text`); índice em SQLite local; geração via `claude -p` (assinatura do Claude Code CLI); transcrições via `yt-dlp`. |
| 🟡 Prazo | 🟡 Nenhum. |
| 🟡 Compliance | 🟡 Uso pessoal e local; o acervo é cópia de estudo e não é redistribuído. |
| 🟡 Orçamento | 🟡 Nenhum custo adicional além da assinatura já existente. |

---

## 7. Dependências externas

- 🟡 Ollama local com o modelo `nomic-embed-text`.
- 🟡 Claude Code CLI autenticado (`claude -p`).
- 🟡 `yt-dlp` para legendas do YouTube.
- 🟡 Acesso à web apenas durante a coleta (sites das fontes e `web.archive.org`).

---

## 8. Riscos

| Risco | Impacto | Probabilidade | Mitigação proposta |
|---|---|---|---|
| 🟡 Pouco material confiável logo após o lançamento | alto | média | lista curada com fontes primárias (docs, blog, podcast do CEO) e peso de confiabilidade |
| 🟡 Vídeo sem legenda extraível | médio | média | registrar falha no relatório; seguir com as demais fontes |
| 🟡 Página original fora do ar ou bloqueando robôs | médio | média | alternativa pelo Internet Archive |
| 🟡 Resposta com alucinação ou sem base no acervo | alto | média | instrução estrita de responder só com os trechos e citar; recusar quando não houver base |
| 🟡 Ollama ou Claude CLI indisponíveis no momento da consulta | médio | baixa | mensagem de erro clara com o passo de correção |

---

## 9. Critérios de aceite (alto nível)

- 🟡 **Dado** a lista curada de fontes, **Quando** o usuário executa a coleta, **Então** o acervo local contém o texto das fontes acessíveis e um relatório lista cada falha com o motivo.
- 🟡 **Dado** o acervo indexado, **Quando** o usuário faz uma pergunta coberta pelas fontes, **Então** recebe resposta em português com citações numeradas que apontam título e URL da fonte.
- 🟡 **Dado** uma pergunta sem base no acervo, **Quando** consultada, **Então** a aplicação declara que o acervo não cobre o tema, em vez de inventar.

---

## Pendências de cobertura

🟡 Nenhuma seção ficou `[INDEFINIDO]`; todas as respostas da entrevista foram "padrão" e estão registradas como premissas 🟡.

---

Gerado por reversa-drafter em 2026-09-22
Fontes: ideation.md, personas.md
