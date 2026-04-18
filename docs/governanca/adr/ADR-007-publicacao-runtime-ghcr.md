# ADR-007 - Publicacao do runtime Hermes em GHCR

Status: Accepted

## Contexto

A ADR-006 criou uma imagem local propria para o runtime de terminal do Hermes,
reduzindo a dependencia direta de `nikolaik/python-nodejs`. Essa etapa melhorou
o controle local, mas ainda nao fechava o ciclo de supply chain: uma tag local
nao atende Modal, Daytona, CI nem ambientes compartilhados que precisam baixar a
mesma imagem por registry e, em ambientes controlados, por digest.

## Problema

Sem uma imagem publicada e versionada:

- cada maquina pode construir uma imagem diferente sob a mesma tag local;
- Modal e Daytona nao conseguem consumir o runtime local;
- CI e ambientes compartilhados ficam sem referencia unica;
- nao ha forma operacional clara de pin por digest.

## Decisao

Padronizar o runtime publicado em GHCR:

```text
ghcr.io/autoarq-paulo/hermes-agent-runtime
```

Tags principais:

- `python3.11-node20`: contrato semantico do runtime;
- `stable`: canal estavel para ambientes que aceitam tag movel;
- `sha-<commit>`: rastreabilidade por commit;
- `<release>-runtime`: tag gerada em push de tag/release.

O default operacional permanece local ate que a publicacao GHCR, a visibilidade
do pacote e o digest sejam validados:

```text
hermes-agent-local:runtime-python3.11-node20
```

GHCR e ativado por opt-in a partir de:

- `HERMES_TERMINAL_RUNTIME_REPOSITORY`;
- `HERMES_TERMINAL_RUNTIME_TAG`;
- `HERMES_TERMINAL_RUNTIME_DIGEST`.

`HERMES_TERMINAL_RUNTIME_IMAGE` continua existindo como override completo para
desenvolvimento local, forks e incidentes. O `docker-compose.yml` local do fork
tambem usa esse caminho explicitamente para manter
`hermes-agent-local:runtime-python3.11-node20`.

## Alternativas consideradas

- Manter somente imagem local: bom para desenvolvimento, insuficiente para CI e
  runtimes remotos.
- Publicar apenas `latest`: simples, mas sem contrato de runtime e sem
  rastreabilidade.
- Usar Docker Hub: funcional, mas GHCR integra melhor com permissoes do GitHub e
  evita credenciais externas alem do `GITHUB_TOKEN`.

## Tradeoffs

- GHCR exige permissao `packages: write` no workflow e pacote visivel/acessivel
  para consumidores remotos.
- GHCR nao e default ate que a primeira publicacao validada seja concluida.
- Tags continuam moveis; ambientes controlados devem configurar digest.
- A namespace `autoarq-paulo` e especifica deste fork e deve ser ajustada por
  forks que publiquem em outra organizacao.

## Impacto em fork/upstream

A mudanca permanece de baixo acoplamento ao core: a logica central so monta
strings de imagem a partir de variaveis de ambiente. O workflow, docs e policy
ficam em camada infra/governanca. Em pulls futuros do upstream, o maior risco de
conflito esta em `hermes_constants.py`, docs e workflows.

## Manutencao futura

- Publicar a imagem via `.github/workflows/runtime-image.yml`.
- Registrar o digest publicado em ambientes controlados com
  `HERMES_TERMINAL_RUNTIME_DIGEST`.
- Atualizar `scripts/check_container_image_policy.py` e
  `runtime_container_policy.md` antes de aprovar novo registry, prefixo ou tag.
- Rodar scanner de imagem no registry final como etapa posterior de compliance.
