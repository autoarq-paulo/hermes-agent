# Publicacao da imagem de runtime Hermes

## Imagem alvo

```text
ghcr.io/autoarq-paulo/hermes-agent-runtime
```

Tags geradas pelo workflow:

- `python3.11-node20`
- `stable`
- `sha-<commit>`
- `<release>-runtime` quando o evento for uma tag Git

## Publicacao por GitHub Actions

Workflow:

```text
.github/workflows/runtime-image.yml
```

Eventos:

- Pull request: build e smoke test, sem push.
- Push em `main`: build multi-arch e push para GHCR.
- Push de tag `v*`: build multi-arch, push e tag `<release>-runtime`.
- `workflow_dispatch`: permite publicar manualmente quando `publish=true`.

Credenciais:

- Usa `GITHUB_TOKEN` com permissao `packages: write`.
- O pacote GHCR precisa estar visivel/acessivel para Modal, Daytona e maquinas
  que executam o Hermes fora do reposititorio.

## Publicacao manual

Use quando estiver fora do GitHub Actions ou validando um hotfix:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile.runtime-python-node \
  -t ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20 \
  -t ghcr.io/autoarq-paulo/hermes-agent-runtime:stable \
  --push .
```

Autenticacao manual:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
```

O token precisa de escopo/permissao de escrita em packages.

## Obtencao do digest

Depois do push:

```bash
docker buildx imagetools inspect ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20
```

Ou, se a imagem foi publicada pelo workflow, leia o campo `Digest` no resumo do
job `Hermes Runtime Image`.

## Ativacao no Hermes

Uso por tag:

```bash
export HERMES_TERMINAL_RUNTIME_REPOSITORY=ghcr.io/autoarq-paulo/hermes-agent-runtime
export HERMES_TERMINAL_RUNTIME_TAG=python3.11-node20
```

Uso por digest:

```bash
export HERMES_TERMINAL_RUNTIME_REPOSITORY=ghcr.io/autoarq-paulo/hermes-agent-runtime
export HERMES_TERMINAL_RUNTIME_TAG=python3.11-node20
export HERMES_TERMINAL_RUNTIME_DIGEST=sha256:<digest>
```

Override local completo:

```bash
export HERMES_TERMINAL_RUNTIME_IMAGE=hermes-agent-local:runtime-python3.11-node20
```

Validacao da resolucao:

```bash
python - <<'PY'
from hermes_constants import get_default_terminal_docker_image
print(get_default_terminal_docker_image())
PY
```

## Modal e Daytona

Modal e Daytona devem usar uma imagem publicada, nao uma tag local. Configure:

```bash
export HERMES_REMOTE_TERMINAL_IMAGE=ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20@sha256:<digest>
```

Ou use os overrides especificos:

```bash
export TERMINAL_MODAL_IMAGE=ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20@sha256:<digest>
export TERMINAL_DAYTONA_IMAGE=ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20@sha256:<digest>
```
