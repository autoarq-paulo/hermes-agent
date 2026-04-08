# ADR-002 - Protecao do Core

Status: Accepted

## Contexto

O mapa arquitetural identifica uma Zona A composta por arquivos que definem o loop do agente, o sistema de tools, a persistencia de sessoes, o bootstrap do CLI e o contrato base do gateway. Alteracoes nesse nivel podem quebrar prompt caching, roteamento, disponibilidade de tools e compatibilidade de sessoes.

## Decisao

Blindar a Zona A como nucleo protegido. Mudancas no core so podem ocorrer com justificativa formal, ADR, teste de regressao e analise de impacto. Extensoes devem entrar por Zona C ou por bordas controladas da Zona B.

## Consequencias

- O core fica mais previsivel.
- O fork ganha uma politica explicita para evitar acoplamento indevido.
- Integracoes externas precisam ser modeladas como tools, adapters ou plugins.
- O custo de mudar o core sobe, mas o risco de quebra estrutural cai.

## Alternativas consideradas

- Permitir alteracao livre no core para acelerar integracoes.
- Tratar todo novo requisito como patch direto em `run_agent.py`.
- Mover protecao do core para convencao informal sem documento normativo.
