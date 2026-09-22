# Investigation: MVP do jev-study

> Identificador: `001-mvp-rag-jev` · Data: 2026-09-22

## Tema: o que é o Jev

O Jev é o primeiro modelo "System One" da TypeSafe AI, fundada por Diogo Almeida (ex-OpenAI, coautor do RLHF), Erik Gafni e Sasha Sheng. Em vez de gerar texto token a token, avalia um estado contra perguntas tipadas (Noul/sim-não, Choice, Score) e devolve resposta com probabilidade e confiança calibradas. É treinado com RLCD (Reinforcement Learning for Calibrated Decisions), que usa regras de pontuação próprias como o Brier score. Lançado em setembro de 2026 sem artigo técnico nem pesos abertos; acesso antecipado por lista de espera.

## Fontes levantadas e nível de confiabilidade

| Fonte | Tier | Observação |
|-------|------|------------|
| https://docs.typesafe.ai/llms.txt | oficial | índice da documentação (primitivas, confiança) |
| https://typesafe.ai/blog/introducing-system-one-models-and-jev | oficial | anúncio |
| https://www.latent.space/p/jev | tecnica | podcast com o CEO |
| https://www.youtube.com/watch?v=cFx9Z3ZXca0 | oficial | "Why We Made Jev", CEO |
| https://pydantic.dev/docs/ai/models/typesafe/ | tecnica | integração Pydantic AI |
| https://docs.litellm.ai/docs/pass_through/typesafe | tecnica | integração LiteLLM |
| https://developers.cloudflare.com/ai/models/typesafe/jev/ | tecnica | ficha do modelo na Cloudflare |
| https://www.langchain.com/blog/building-a-harness-with-jev | tecnica | guia LangChain |
| https://techcrunch.com/2026/09/18/a-new-kind-of-ai-model-from-a-chatgpt-inventor-is-thrilling-developers/ | imprensa | TechCrunch |
| https://www.tomshardware.com/tech-industry/artificial-intelligence/typesafe-ais-jev-offers-an-alternative-to-llms-that-claims-to-be-193x-faster-and-445x-cheaper-system-one-type-model-is-bespoke-for-probabilistic-decision-making | imprensa | Tom's Hardware |
| https://www.mindstudio.ai/blog/jev-system-one-model-launch | divulgacao | explicação de terceiro |
| https://lilting.ch/en/articles/typesafe-ai-jev-system-one-model | divulgacao | comparação com MDLM |

Excluídos: reposts sem autoria, vídeos "BREAKING" de canais agregadores, repositórios que alegam superar o Jev sem verificação independente.

## Alternativas avaliadas

- **Chroma / LanceDB:** mais recursos; excessivo para centenas de trechos.
- **sqlite-vec:** exige extensão carregável; o `sqlite3` do Python do macOS pode não permitir `enable_load_extension`.
- **youtube-transcript-api:** frágil diante de mudanças do YouTube; `yt-dlp` já está instalado e é mais mantido.
- **Ollama como gerador (qwen3:8b):** local; qualidade inferior ao Claude e o usuário pediu a assinatura.

## Padrões aplicáveis

- Prefixos de tarefa do nomic-embed (`search_document:` / `search_query:`).
- Citações numeradas com lista filtrada pelos números efetivamente citados.
- Recusa por limiar antes da geração (evita alucinação e poupa cota).
