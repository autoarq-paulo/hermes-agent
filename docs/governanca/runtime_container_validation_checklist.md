# Checklist de validacao da imagem de runtime

Use este checklist quando alterar `docker/Dockerfile.runtime-python-node`,
defaults de terminal ou politica de imagens.

## 1. Build local

```bash
docker build -f docker/Dockerfile.runtime-python-node -t hermes-agent-local:runtime-python3.11-node20 .
```

Validar versoes:

```bash
docker run --rm hermes-agent-local:runtime-python3.11-node20 python --version
docker run --rm hermes-agent-local:runtime-python3.11-node20 node --version
docker run --rm hermes-agent-local:runtime-python3.11-node20 npm --version
```

Esperado:

- Python 3.11.x
- Node.js v20.x
- npm funcional

## 1.1 Build via Compose

```bash
docker compose --profile runtime build hermes-runtime
```

## 2. Execucao local via Docker backend

```bash
TERMINAL_ENV=docker \
TERMINAL_DOCKER_IMAGE=hermes-agent-local:runtime-python3.11-node20 \
python - <<'PY'
import json
from tools.terminal_tool import terminal_tool

result = json.loads(terminal_tool("python --version && node --version && npm --version", task_id="runtime-policy-check"))
print(result["output"])
raise SystemExit(result["exit_code"])
PY
```

## 3. Configuracao do CLI

```bash
python - <<'PY'
from cli import load_cli_config
cfg = load_cli_config()
print(cfg["terminal"]["docker_image"])
print(cfg["terminal"]["singularity_image"])
print(cfg["terminal"]["modal_image"])
print(cfg["terminal"]["daytona_image"])
PY
```

Esperado:

- Em execucao normal sem registry opt-in, Docker aponta para
  `hermes-agent-local:runtime-python3.11-node20`.
- Singularity aponta para
  `docker://hermes-agent-local:runtime-python3.11-node20`.
- Quando `HERMES_TERMINAL_RUNTIME_REPOSITORY` estiver configurado, Docker,
  Modal e Daytona passam a apontar para a imagem publicada ou digest fixado.

Validar digest:

```bash
HERMES_TERMINAL_RUNTIME_DIGEST=sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
HERMES_TERMINAL_RUNTIME_REPOSITORY=ghcr.io/autoarq-paulo/hermes-agent-runtime \
python - <<'PY'
from hermes_constants import get_default_terminal_docker_image
print(get_default_terminal_docker_image())
PY
```

Esperado: referencia terminando em `@sha256:aaaa...`.

## 4. Referencias antigas

```bash
python scripts/check_container_image_policy.py
```

Esperado: `Container image policy check passed.`

## 5. Teste automatizado

```bash
source venv/bin/activate
python -m pytest tests/governanca/test_container_image_policy.py tests/tools/test_terminal_tool.py -q
```

## 6. Checagem basica de seguranca

Opcional, se a ferramenta estiver instalada:

```bash
trivy image hermes-agent-local:runtime-python3.11-node20
```

Sem Trivy, registre no PR/release que a checagem de vulnerabilidade ficou
pendente e execute no pipeline que tiver scanner de imagens.

## 7. Publicacao

Checklist:

- `docker buildx` disponivel.
- Login no GHCR feito com token que possa escrever packages.
- Workflow `.github/workflows/runtime-image.yml` habilitado.
- `docker buildx imagetools inspect` mostra a tag publicada.
- Digest registrado no ambiente controlado.

Publicacao manual:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile.runtime-python-node \
  -t ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20 \
  -t ghcr.io/autoarq-paulo/hermes-agent-runtime:stable \
  --push .
docker buildx imagetools inspect ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20
```

## 8. Cloud backends

Modal e Daytona precisam de imagem em registry:

```bash
export HERMES_REMOTE_TERMINAL_IMAGE=ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20@sha256:<digest>
```

Depois configure:

```bash
export TERMINAL_MODAL_IMAGE="$HERMES_REMOTE_TERMINAL_IMAGE"
export TERMINAL_DAYTONA_IMAGE="$HERMES_REMOTE_TERMINAL_IMAGE"
```

Valide com os testes de integracao correspondentes apenas em ambiente com
credenciais reais:

```bash
TERMINAL_ENV=modal python -m pytest tests/integration/test_modal_terminal.py -q
TERMINAL_ENV=daytona python -m pytest tests/integration/test_daytona_terminal.py -q
```
