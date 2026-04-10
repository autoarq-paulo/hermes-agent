# Comentarios de Intencao

## Regra

Quando um trecho existir como fallback tecnico, compatibilidade temporaria, workaround, placeholder, excecao controlada ou mitigacao local, o comentario deve deixar clara a intencao e o limite da decisao.

## Como comentar

- Curto.
- Tecnico.
- Explicita o motivo da existencia.
- Explicita o que o trecho nao representa.
- Explicita quando revisar ou remover.

## O que comentar

- Fallbacks que poderiam parecer endpoint, contrato ou fluxo definitivo.
- Excecoes controladas para evitar tocar no core em excesso.
- Compatibilidades transitivas que protegem uma migracao em andamento.
- Pontos de extensao do fork que nao devem ser confundidos com baseline do Hermes.

## O que evitar

- Comentario obvio de sintaxe.
- Texto vago que nao esclarece a decisao.
- Comentario que pareca documentacao de marketing.
- Repetir em excesso o que a doc de governanca ja cobre.

## Quando documentar tambem

- Se a decisao afetar arquitetura, contrato publico, discovery, extensao ou estrategia de integracao, registrar tambem em `docs/governanca/`.
- Se for apenas local e tecnico, o comentario pode bastar, desde que a intencao fique inequivoca.
