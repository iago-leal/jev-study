# Ideation, jev-study

> Selo 🟡 PLANEJADO em todos os itens, sujeito a validação.

## Brief original
Quero construir uma pequena aplicação que consiste em buscar, pode ser no archive, alguns vídeos no YouTube e documentações do próprio Jev AI, para eu poder estudar sobre essa nova modalidade de inteligência artificial. Podemos, inclusive, criar um RAG bem levinho para que o que eu faço de pergunta possa ser consultado diretamente nele, sem necessidade de novas rodadas de buscas na web. Busque por fontes confiáveis no assunto.

## Problema
🟡 O Jev, da TypeSafe AI, primeiro modelo da classe "System One" (decisões tipadas com probabilidade e confiança, sem geração autorregressiva de texto), foi lançado em setembro de 2026. O material sobre ele é novo e está disperso entre documentação oficial, blog da empresa, podcasts, vídeos no YouTube e imprensa técnica. Não há artigo técnico nem pesos abertos. Quem quer estudá-lo precisa refazer buscas na web a cada dúvida e separar, por conta própria, fonte primária de texto promocional.

## Valor entregue
🟡 Fazer perguntas em linguagem natural sobre o Jev e receber respostas fundamentadas em um acervo local e curado, sempre com a fonte citada, sem nova rodada de busca na web.

## Alternativas existentes
🟡 NotebookLM: exige carregar as fontes manualmente, depende de serviço externo e não aplica hierarquia de confiabilidade entre fontes.
🟡 Busca manual (web e YouTube): repetitiva, lenta a cada pergunta e sem registro reaproveitável do que já foi lido.

## Público-alvo (bruto)
🟡 O próprio usuário, em uso local e individual: médico e desenvolvedor que estuda IA aplicada.

## Métricas de sucesso
🟡 Respostas com citação correta: 80% das perguntas de um conjunto de avaliação respondidas com pelo menos uma citação que de fato sustenta a resposta.

## Premissas a validar
🟡 Há material confiável suficiente logo após o lançamento para sustentar um acervo útil.
🟡 Os vídeos relevantes do YouTube têm legenda (manual ou automática) extraível; sem ela, não entram no acervo.
🟡 A documentação oficial (docs.typesafe.ai, com índice `/llms.txt`) permanece acessível; caso contrário, recorre-se ao Internet Archive.

## Notas
🟡 O usuário mencionou o "archive" como fonte: o Internet Archive (Wayback Machine) entra como alternativa de coleta quando a página original falhar.
🟡 A geração das respostas usa a assinatura do Claude Code CLI (`claude -p`), não chave de API.
🟡 Leitura alternativa descartada na entrevista: JEPA (Yann LeCun). O tema confirmado é o Jev, da TypeSafe AI.

---
Gerado por reversa-ideator em 2026-09-22T00:00:00-03:00
Fonte: newproject-brief.md (entrevista única do modo expresso)
