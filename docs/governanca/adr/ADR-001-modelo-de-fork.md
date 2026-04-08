# ADR-001 - Modelo de Fork

Status: Accepted

## Contexto

O Hermes Agent tem um core central, uma camada de tools, gateway multiplaforma e varios pontos de extensao. Um fork que mistura customizacoes com o baseline perde previsibilidade, dificulta updates e aumenta o risco de regressao.

## Decisao

Adotar o modelo de `upstream` como origem oficial, `main` limpa como baseline de referencia e branches de adaptacao para customizacoes locais. O `main` do fork deve acompanhar o `upstream/main` com o minimo de divergencia possivel.

## Consequencias

- Atualizacoes de upstream ficam mais simples e mais seguras.
- Customizacoes locais ficam isoladas em branches ou modulos especificos.
- Fica mais facil identificar o que e delta do fork e o que veio do projeto original.
- A disciplina de branches passa a ser um requisito operacional.

## Alternativas consideradas

- Manter um unico `main` com tudo misturado.
- Manter uma arvore de patches sobre o upstream.
- Congelar o upstream e evoluir o fork de forma totalmente independente.

