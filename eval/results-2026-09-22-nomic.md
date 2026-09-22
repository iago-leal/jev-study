# Avaliação do jev-study (2026-09-22)

Respostas com ao menos uma citação: 9/10 (90%).
Meta do PRD: ≥ 80% com citação que de fato sustenta a resposta. Marque abaixo as corretas.

## 1. O que é um modelo System One e em que ele difere de um LLM?

**Status:** respondida

Um modelo System One é uma classe de modelo de IA construída para tomar decisões rápidas e estruturadas que o software pode usar diretamente: ele avalia um *state* (estado/contexto) e retorna respostas tipadas e probabilidades [1][4]. Jev é o modelo carro-chefe da TypeSafe e o primeiro modelo System One [1].

Quanto à diferença em relação a um LLM, os trechos apontam três pontos centrais:

1. **Natureza da saída**: como um LLM, o System One compreende entrada em linguagem natural, mas, diferentemente dele, não escreve respostas, não produz código nem gera explicações de seu raciocínio — retorna decisões tipadas e probabilidades [1][4]. As respostas possíveis são definidas por meio de "primitivos" (*primitives*), como Choice (escolha entre opções), Score (pontuação em níveis ordenados) e Noul (verdadeiro/falso, expresso como probabilidade) [1][4].

2. **Treinamento e calibração**: System One models são treinados para decisões calibradas, isto é, suas probabilidades são otimizadas contra resultados reais para refletir incerteza. Essa calibração é medida em grupos de previsões, não garantindo que uma resposta individual isolada esteja correta [1].

3. **Escopo de entrada**: atualmente, Jev aceita apenas texto — strings, objetos JSON e arrays de texto —, sem suporte a imagens, áudio ou vídeo [1].

Há também um trecho de tier "tecnica" (blog da LangChain) que complementa essa descrição, afirmando que o treinamento usa "reinforcement learning for calibrated decisions (RLCD)" e que o código da aplicação usa os resultados para guiar a próxima ação de um agente, sem exigir uma chamada completa a um LLM de chat a cada decisão [5]. Como esse detalhe (a sigla RLCD e o mecanismo de treinamento específico) não aparece em nenhum trecho de tier "oficial", não posso confirmá-lo com a documentação da TypeSafe — os trechos oficiais mencionam apenas que as probabilidades são "otimizadas contra resultados" [1], sem especificar a técnica de treinamento. Fica como divergência/complemento não verificado pela fonte oficial.

Por fim, o nome "System One" remete ao conceito popularizado por Daniel Kahneman em *Thinking, Fast and Slow*: o "Sistema 1" é rápido e intuitivo, em contraste com o "Sistema 2", mais lento e deliberado; aqui a ênfase está em julgamentos rápidos e focados [4].

**Fontes citadas:**
- [1] Documentação oficial da TypeSafe AI: System One (oficial) https://docs.typesafe.ai/concepts/system-one.md
- [4] Documentação oficial da TypeSafe AI: System One (oficial) https://docs.typesafe.ai/concepts/system-one.md
- [5] What Is Jev? A Guide to TypeSafe AI's System One Model (LangChain) (tecnica) https://www.langchain.com/blog/building-a-harness-with-jev

- [ ] As citações sustentam a resposta

## 2. Quais são os tipos de pergunta (primitivas) que o Jev aceita e quando usar cada um?

**Status:** recusada (abaixo do limiar)

O acervo não cobre essa pergunta.

- [ ] As citações sustentam a resposta

## 3. Como o Jev expressa confiança, e como devo usar esse valor na arquitetura de um sistema?

**Status:** respondida

Os trechos fornecidos não abordam diretamente como o Jev expressa ou comunica sua confiança (não há descrição do formato do valor de confiança, escala, ou mecanismo de exposição na resposta da API). O que os trechos confirmam é o seguinte:

O Jev retorna, junto com decisões tipadas, probabilidades calibradas — ou seja, sua saída inclui um valor numérico de confiança otimizado para refletir incerteza real, e não apenas texto gerado [4]. Essa calibração é medida sobre grupos de previsões, o que significa que ela garante acurácia agregada, mas não assegura que uma resposta individual esteja correta [4].

Quanto ao uso arquitetural desse valor, os trechos indicam explicitamente um caso: ao trabalhar com conteúdo em idiomas diferentes do inglês (idioma primário de treinamento, com acurácia inferior em outras línguas, incluindo scripts CJK), a documentação recomenda prestar atenção à confiança "ao rotear" — isto é, usar o valor de confiança como critério de decisão sobre o que fazer com a resposta do modelo, por exemplo, decidir se ela deve ser aceita diretamente ou encaminhada para outro tratamento [2][5].

O que falta nos trechos para uma resposta mais completa:
- Não há descrição do formato exato do valor de confiança (se é uma probabilidade de 0 a 1, um score categórico, etc.).
- Não há explicação de como esse valor é calculado ou exposto na resposta da API (nome do campo, estrutura JSON).
- Não há orientação arquitetural mais ampla sobre thresholds recomendados, fallback para revisão humana, ou combinação com chamadas de raciocínio (embora o trecho [3] mencione, em tom de podcast/técnico, a ideia de combinar múltiplas chamadas Jev com uma chamada de raciocínio, isso é uma reflexão informal de Diogo Almeida e não trata especificamente de confiança, mas sim de economia de custo).

**Fontes citadas:**
- [2] Documentação oficial da TypeSafe AI: Models (oficial) https://docs.typesafe.ai/models.md
- [3] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev
- [4] Documentação oficial da TypeSafe AI: System One (oficial) https://docs.typesafe.ai/concepts/system-one.md
- [5] Documentação oficial da TypeSafe AI: State (oficial) https://docs.typesafe.ai/concepts/state.md

- [ ] As citações sustentam a resposta

## 4. O que é o campo state numa requisição ao Jev?

**Status:** respondida

O campo `state` é o objeto de entrada que reúne o conteúdo e os fatos de apoio sobre os quais o Jev deve julgar — pode ser uma string, um objeto JSON ou um array de valores de texto [3]. Ele é ingerido uma única vez, e todas as perguntas (`questions`) da requisição são avaliadas contra esse mesmo `state` em paralelo [3].

Ao construir o `state`, deve-se agrupar nele informações relacionadas sempre que a decisão exigir comparar essas partes entre si — por exemplo, uma conversa de suporte, um pedido e uma política de reembolso podem compor um único `state`, mesmo contendo elementos distintos, desde que a análise dependa de cruzá-los [1]. O `state` concentra o conteúdo e os fatos; já os julgamentos a serem feitos sobre esse material ficam a cargo das perguntas definidas separadamente, nas primitivas de pergunta [1].

Recomenda-se usar JSON aninhado tanto para `state` quanto para `questions`, podendo-se apontar uma pergunta para um valor específico dentro do `state` por meio de um caminho com crases, como `` `support.tickets[0].message` `` [4].

Em termos de limites, o orçamento de contexto de 32k tokens cobre o `state` somado à pergunta mais longa isoladamente, enquanto o limite de 64k tokens cobre o `state` somado a todas as perguntas combinadas [3][6]. Quanto ao conteúdo aceito, o `state` deve ser texto: entradas não textuais, como imagens, áudio ou vídeo, precisam ser pré-processadas em texto ou campos estruturados antes de serem enviadas como `state`, pois o Jev não aceita esses formatos diretamente [3][5].

Por fim, é no `state` que se deve colocar o conteúdo proprietário, os registros e o material de referência do domínio do usuário, já que o modelo não é ajustado por conta — a especialização ocorre via requisição, combinando `state` com `instructions` e `criteria` das perguntas [5].

**Fontes citadas:**
- [1] Documentação oficial da TypeSafe AI: State (oficial) https://docs.typesafe.ai/concepts/state.md
- [3] Documentação oficial da TypeSafe AI: Models (oficial) https://docs.typesafe.ai/models.md
- [4] Documentação oficial da TypeSafe AI: How to build with TypeSafe (oficial) https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- [5] Documentação oficial da TypeSafe AI: Models (oficial) https://docs.typesafe.ai/models.md
- [6] Documentação oficial da TypeSafe AI: Models (oficial) https://docs.typesafe.ai/models.md

- [ ] As citações sustentam a resposta

## 5. O que é RLCD e como ele difere do RLHF?

**Status:** respondida

RLCD (Reinforcement Learning from Calibrated Decisions) é definido pela documentação oficial como um paradigma que otimiza um contrato de saída diferente do RLHF: o modelo não gera texto, mas retorna decisões e probabilidades, e uma probabilidade maior deve corresponder a uma chance maior de a resposta estar correta [6]. A calibração é o que torna a incerteza utilizável por software: em um modelo bem calibrado, previsões com probabilidade 0,2 devem ocorrer cerca de 20% das vezes, as de 0,8 cerca de 80%, e as de 1,0 devem ocorrer 100% das vezes — sendo taxas que descrevem grupos de previsões, não uma garantia sobre uma resposta isolada [6].

Já o RLHF é tratado nos trechos como algo que se ramifica em diferentes linhagens históricas. Diogo Almeida remete a três marcos: o trabalho de demonstração de backflip de robô (Christiano et al. 2017), o "learning to summarize" da OpenAI e o InstructGPT (Ouyang et al. 2022), do qual ele foi coautor [3][4]. Ele esclarece que, quando fala em RLHF, refere-se especificamente à tarefa de seguir instruções ("instruction following"), não ao mecanismo de otimização por PPO em si — o ponto central é o "north star" que essa tarefa estabelece, e é justamente aí que o RLCD se propõe como uma tarefa nova e distinta [4][5].

Quanto à diferença conceitual, o material oficial mostra que os caminhos de treinamento se ramificam a partir de modelos de linguagem pré-treinados em rotas de RLHF e RLVR (apresentadas de forma atenuada no diagrama) e uma rota de RLCD, destacada como o caminho para um "modelo de decisão" ("decision-model path") [6]. Isso indica que o RLCD não é uma variação do RLHF, mas uma alternativa com objetivo distinto: onde o RLHF orienta a geração textual segundo preferências humanas, o RLCD orienta a produção de decisões calibradas probabilisticamente [6].

Os trechos de tier "tecnica" (Latent Space) complementam essa distinção com a justificativa filosófica de Diogo: ele argumenta que treinar com dados de usuários reais tende a gerar overfitting ao presente, devido à lei de potência de perguntas repetidas, e que RLHF "puro" tende a produzir comportamentos indesejados como sicofania (ele mesmo hesita sobre o termo exato: "Sycophancy, psychophancy... eu não sei, seja qual for a palavra") [1][2][3]. Ele afirma que RLHF, RLVR e as inovações subsequentes (function calling, structured outputs, reasoning) são, em sua visão, "hacks" sobre o paradigma de previsão sequência-a-sequência baseado em strings, e que o RLCD nasceu de sua tentativa, entre 2023 e 2024, de resolver o problema central de confiabilidade ("reliability") que via nesse paradigma [3].

Uma ressalva sobre os trechos: eles não fornecem uma definição formal, passo a passo, do mecanismo de treinamento do RLCD (como funciona o processo de otimização, que tipo de sinal de recompensa usa), nem detalham tecnicamente por que RLVR também é considerado insuficiente frente ao RLCD — o material apenas indica que RLVR aparece "atenuado" no mesmo diagrama de ramificação [6]. Além disso, não há confirmação, nos trechos fornecidos, de que exista publicação acadêmica formal sobre o RLCD: o próprio Diogo afirma, na entrevista, que "ainda não" publicou nada a respeito [5].

**Fontes citadas:**
- [1] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev
- [2] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev
- [3] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev
- [4] Why I couldn't build Jev at OpenAI — Diogo Almeida, TypeSafe Co-founder & CEO (oficial) https://www.youtube.com/watch?v=cFx9Z3ZXca0&t=1689s
- [5] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev
- [6] Documentação oficial da TypeSafe AI: AI primer (oficial) https://docs.typesafe.ai/introduction/machine-learning-primer.md

- [ ] As citações sustentam a resposta

## 6. Quanto o Jev é mais rápido e mais barato que um LLM, segundo a TypeSafe, e quem verificou esses números?

**Status:** respondida

Os trechos não trazem uma comparação de velocidade e custo do modelo `jev-latest` diretamente contra um LLM verificada oficialmente — o que há é uma ressalva explícita nesse sentido, mais dois conjuntos de números correlatos.

Sobre latência bruta, a TypeSafe reporta round-trip médio de 111ms, contra 1,1 a 13,9 segundos por chamada dos LLMs testados, nas configurações de concorrência do cookbook [1]. Isso dá uma ordem de grandeza (dezenas de vezes mais rápido), mas o próprio trecho não calcula um fator único de "quantas vezes mais rápido".

Já o cookbook de custo e velocidade por rubrica apresenta colunas `vs ts_choice` que dividem tempo e custo de cada condição pelos números da TypeSafe, mas o número relativo em si (quantas vezes) depende da saída do código e não está impresso no trecho [2]. Além disso, esse mesmo trecho contém a ressalva central para sua pergunta: os custos usam "as premissas históricas de preço do Setup, incluindo a taxa `speed_latest` para a TypeSafe", e "não são preços `jev-latest` verificados nem valores de cobrança atuais" [2]. Ou seja, a própria documentação oficial adverte que esses números de custo não foram verificados como correntes.

Também vale notar uma divergência de nomenclatura nos dois cookbooks: a chamada solicita o modelo `jev-latest`, mas o modelo efetivamente retornado nas 15 chamadas foi `jev-1.13.0` [2]; o cookbook de nouls, por sua vez, afirma que a execução "usa `jev-latest` na API de produção" [5]. Ambos são tier oficial, então não há um tier inferior a descartar aqui — mas a discrepância entre o nome da versão solicitada e a retornada é algo a registrar.

Sobre quem verificou: nenhum trecho indica auditoria externa. A demo de smart home apenas descreve, em prosa qualitativa, que "a resposta inicial da TypeSafe é tão rápida comparada à resposta do LLM que adiciona latência desprezível ao sistema geral" [3], sem números nem verificação. A Introdução também não traz números, apenas o conceito de modelo "System One" [4].

**Falta nos trechos**: um fator numérico único e verificado de "X vezes mais rápido / mais barato" que a TypeSafe atribua ao Jev frente a um LLM; a própria fonte oficial declara que os números de custo apresentados não são preços `jev-latest` verificados [2], e nenhum trecho menciona verificação por terceiros.

**Fontes citadas:**
- [1] Documentação oficial da TypeSafe AI: Self-consistency: nouls (oficial) https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md
- [2] Documentação oficial da TypeSafe AI: Self-consistency: choices (oficial) https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md
- [3] Documentação oficial da TypeSafe AI: Smart home assistant demo (oficial) https://docs.typesafe.ai/demos/smart-home.md
- [4] Documentação oficial da TypeSafe AI: Introduction (oficial) https://docs.typesafe.ai/introduction.md
- [5] Documentação oficial da TypeSafe AI: Self-consistency: nouls (oficial) https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md

- [ ] As citações sustentam a resposta

## 7. Quais são as limitações conhecidas do Jev?

**Status:** respondida

As limitações conhecidas do jev-1.13 estão documentadas oficialmente pela TypeSafe AI [2][3].

De modo geral, o modelo é rápido, calibrado e bom em julgamento de senso comum, mas não é perfeito: apresenta desempenho ótimo em tarefas do tipo "System One" e pode falhar em tarefas que exigem níveis adicionais de indireção, além de ser bastante literal em sua interpretação [2].

**Leitura literal**: jev-1.13 responde à pergunta que foi escrita, não à que foi pretendida. Palavras de escopo, negações e condições implícitas são lidas ao pé da letra, de modo que a resposta se baseia nas palavras da instrução, e não na intenção por trás delas [3].

**Matemática e números**: o modelo não é uma calculadora. A documentação recomenda fortemente implementar qualquer lógica matemática em código, já que o desempenho é melhor em questões semânticas do que em questões matemáticas [3].

**Contagem**: jev-1.13 não conta de forma confiável — isso abrange caracteres em uma palavra, ocorrências de um termo em um trecho e itens em listas longas. O modelo reconhece o formato de uma resposta em vez de efetivamente contar, e o erro cresce conforme aumenta o tamanho daquilo que está sendo contado [3].

Os trechos oficiais também indicam a existência de uma tabela mais ampla de "failure modes", numerada de 1 a pelo menos 9, mas apenas os itens 1 (Literal reading), 2 (Math and Numbers) e a entrada 9 (Generation, cuja recomendação é "use a generative model") aparecem nos trechos fornecidos; o conteúdo detalhado dos itens 3 a 8 não está disponível no material recebido, de modo que não posso descrever essas limitações adicionais [2][3].

**Fontes citadas:**
- [2] Documentação oficial da TypeSafe AI: Jev 1.13 jaggedness (oficial) https://docs.typesafe.ai/model-jaggedness/jev-1.13.md
- [3] Documentação oficial da TypeSafe AI: Jev 1.13 jaggedness (oficial) https://docs.typesafe.ai/model-jaggedness/jev-1.13.md

- [ ] As citações sustentam a resposta

## 8. Por que Diogo Almeida diz que não conseguiria construir o Jev dentro da OpenAI?

**Status:** respondida

Os trechos fornecidos não contêm uma declaração de Diogo Almeida afirmando explicitamente que não conseguiria construir o Jev dentro da OpenAI. Não há, nos excertos numerados, nenhuma passagem em que ele compare diretamente a viabilidade do Jev com uma hipotética permanência na OpenAI.

O que os trechos mostram é algo relacionado, mas distinto: Almeida descreve ter escolhido "o caminho difícil" ao recusar-se a fazer benchmarking convencional mesmo sob pressão de investidores durante a captação de recursos [5], e Swyx comenta que, ao optar por esse caminho, ele "acaba construindo a empresa em que quer trabalhar", contrastando isso com "vender-se" e "trabalhar na OpenAI, mas com meu pessoal" [5]. Almeida concorda e diz não ter muitos arrependimentos [5]. Esse trecho sugere uma tensão entre os princípios que guiaram o desenvolvimento do Jev (recusa a benchmarks, construção de confiança de longo prazo) e a cultura que ele atribui a laboratórios como OpenAI e Anthropic, aos quais se refere como não sendo "especialistas cientes da verdadeira opcionalidade disponível" [6].

Para responder com precisão à pergunta como formulada, faltaria um trecho em que Almeida declare de modo direto a impossibilidade de ter construído o Jev na OpenAI — por exemplo, explicando restrições institucionais, de incentivos ou de cultura específicas daquela empresa que o teriam impedido.

**Fontes citadas:**
- [5] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev
- [6] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev

- [ ] As citações sustentam a resposta

## 9. Como integrar o Jev com o Pydantic AI?

**Status:** respondida

Os trechos fornecidos não contêm informação suficiente para responder a essa pergunta. Há apenas uma menção de que o Jev possui integrações com "outras SDKs" e também SDKs próprias, sem qualquer detalhe sobre Pydantic ou Pydantic AI especificamente [6].

Falta um trecho que aborde diretamente a integração do Jev com Pydantic AI — por exemplo, documentação oficial sobre esse SDK específico ou um cookbook/pattern que trate do assunto.

**Fontes citadas:**
- [6] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev

- [ ] As citações sustentam a resposta

## 10. Em que casos de uso o Jev não é indicado?

**Status:** respondida

Os trechos fornecidos não tratam diretamente de casos de uso nos quais o Jev *não* seria indicado. Eles descrevem para que o modelo foi otimizado — intelligence per dollar, calibração de confiança e decisões calibradas via RLCD [2][5] — e listam exemplos de aplicações onde é usado, como jogos, computer use, coding agents, linting, análise de "dark data", entity resolution e busca em linguagem natural [4], além do primitivo de pontuação com scores e probabilidades calibradas [6]. Também há registro de que ele não é ajustado por fine-tuning ou LoRA com dados de clientes, sendo moldado via requisição, e não por pesos específicos de conta [2].

Falta nos trechos: qualquer afirmação explícita da TypeSafe AI ou de terceiros sobre limitações de uso, cenários desaconselhados, restrições declaradas de escopo ou avisos de "não use para X". Para responder com precisão a essa pergunta, seria necessário um trecho — de preferência tier oficial — que trate especificamente de limitações, avisos de uso ou contraindicações do Jev.

**Fontes citadas:**
- [2] Documentação oficial da TypeSafe AI: Models (oficial) https://docs.typesafe.ai/models.md
- [4] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev
- [5] Jev: System One models for Prod, not God — Latent Space (tecnica) https://www.latent.space/p/jev
- [6] Documentação oficial da TypeSafe AI: Score (oficial) https://docs.typesafe.ai/primitives/score.md

- [ ] As citações sustentam a resposta
