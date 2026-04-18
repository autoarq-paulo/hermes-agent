# Rollback da imagem de runtime

Este plano existe para incidentes de compatibilidade apos trocar o runtime de
terminal. Use rollback apenas como mitigacao temporaria e abra issue/ADR para
registrar a causa.

## Sinais que justificam rollback

- Docker backend nao cria container mesmo apos rebuild limpo.
- Comandos que exigem Python 3.11 ou Node.js 20 falham na inicializacao.
- Modal/Daytona nao conseguem baixar a imagem publicada no registry.
- Uma regressao bloqueia operacao critica e nao ha correcao rapida no Dockerfile.

## Retorno rapido para imagem local

Sem alterar codigo, sobrescreva a imagem publicada por ambiente:

```bash
export HERMES_TERMINAL_RUNTIME_IMAGE="hermes-agent-local:runtime-python3.11-node20"
unset HERMES_TERMINAL_RUNTIME_DIGEST
```

## Retorno para tag publicada anterior

```bash
export HERMES_TERMINAL_RUNTIME_REPOSITORY=ghcr.io/autoarq-paulo/hermes-agent-runtime
export HERMES_TERMINAL_RUNTIME_TAG=<tag-anterior>
unset HERMES_TERMINAL_RUNTIME_DIGEST
unset HERMES_TERMINAL_RUNTIME_IMAGE
```

## Sair de digest fixado

Se o digest fixado estiver quebrado, mas a tag publicada ja foi corrigida:

```bash
unset HERMES_TERMINAL_RUNTIME_DIGEST
```

## Retorno emergencial para a imagem antiga

Use apenas se a imagem propria e a tag publicada falharem e a operacao estiver
bloqueada:

```bash
export TERMINAL_DOCKER_IMAGE="nikolaik/python-nodejs:python3.11-nodejs20"
export TERMINAL_SINGULARITY_IMAGE="docker://nikolaik/python-nodejs:python3.11-nodejs20"
export TERMINAL_MODAL_IMAGE="nikolaik/python-nodejs:python3.11-nodejs20"
export TERMINAL_DAYTONA_IMAGE="nikolaik/python-nodejs:python3.11-nodejs20"
```

Ou em `~/.hermes/config.yaml`:

```yaml
terminal:
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  singularity_image: "docker://nikolaik/python-nodejs:python3.11-nodejs20"
  modal_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  daytona_image: "nikolaik/python-nodejs:python3.11-nodejs20"
```

Importante: esse rollback reintroduz a dependencia de terceiro nao oficial.
Remova o override assim que a imagem propria for corrigida.

## Arquivos a reverter em rollback de codigo

Se a correcao exigir revert parcial, revise estes arquivos:

- `hermes_constants.py`
- `cli.py`
- `hermes_cli/config.py`
- `hermes_cli/setup.py`
- `hermes_cli/status.py`
- `tools/terminal_tool.py`
- `docker-compose.yml`
- `cli-config.yaml.example`
- `docker/Dockerfile.runtime-python-node`
- `scripts/check_container_image_policy.py`

## Pos-rollback

1. Registre o motivo do rollback no changelog/issue.
2. Rode `python scripts/check_container_image_policy.py` e documente a excecao
   se o override antigo precisar permanecer por mais de uma sessao operacional.
3. Corrija o Dockerfile ou publique nova tag/digest.
4. Remova os overrides e rode o checklist de validacao novamente.
