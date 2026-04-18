# Politica de imagem de runtime do Hermes

## Escopo

Esta politica cobre imagens usadas pelo terminal runtime e sandboxes
correlatos: Docker, Singularity/Apptainer, Modal e Daytona.

## Requisitos minimos

- Python 3.11 disponivel como `python`.
- Node.js 20 disponivel como `node`.
- `npm` e `npx` disponiveis para bootstrap JavaScript.
- `bash`, `git`, `curl`, `wget`, `jq`, `ripgrep`, `procps`, `zip`, `unzip` e
  certificados CA instalados.
- Base oficial ou explicitamente aprovada em ADR.
- Build reproduzivel por Dockerfile versionado no repositorio.

## Imagem aprovada

Runtime local aprovado e default operacional enquanto a publicacao GHCR nao
for validada:

```text
hermes-agent-local:runtime-python3.11-node20
```

Repositorio publicado aprovado para opt-in:

```text
ghcr.io/autoarq-paulo/hermes-agent-runtime
```

Tag semantica padrao:

```text
python3.11-node20
```

Dockerfile:

```text
docker/Dockerfile.runtime-python-node
```

## Tags aprovadas

- `python3.11-node20`: contrato semantico do runtime.
- `stable`: canal estavel movel.
- `sha-<commit>`: rastreabilidade por commit.
- `<release>-runtime`: tag de release.

Ambientes controlados devem preferir digest:

```text
ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20@sha256:<digest>
```

## Criterios de seguranca

- Preferir imagens oficiais e slim.
- Evitar pacotes que nao sejam necessarios ao contrato minimo.
- Limpar caches de `apt`, `pip` e `npm`.
- Nao embutir credenciais, tokens, certificados privados ou dados de usuario.
- Usar digest para promocao em CI/producao quando o registry final existir.
- Manter comentarios de intencao para qualquer fallback tecnico.

## Prefixos permitidos

Referencias diretas em arquivos criticos so podem usar:

- `ghcr.io/autoarq-paulo/hermes-agent-runtime:<tag>`;
- `docker://ghcr.io/autoarq-paulo/hermes-agent-runtime:<tag>`;
- `hermes-agent-local:runtime-python3.11-node20`;
- `docker://hermes-agent-local:runtime-python3.11-node20`;
- bases Docker oficiais ou explicitamente aprovadas em
  `scripts/check_container_image_policy.py`.

Prefixos proibidos por padrao:

- `nikolaik/python-nodejs`;
- imagens de usuario/organizacao nao documentadas;
- tags `latest` para runtime de terminal;
- imagens sem contrato de runtime Python 3.11 + Node 20.

## Usuario do container

O runtime atual permanece root por compatibilidade com o backend Docker do
Hermes, que monta `/root` e permite instalacao sob demanda dentro do sandbox.
Esse nao e o desenho final desejado; e um compromisso delimitado enquanto
`DockerEnvironment` nao tiver suporte completo a home/workspace non-root.

Mitigacoes atuais:

- `DockerEnvironment` aplica `--cap-drop ALL`.
- `DockerEnvironment` aplica `--security-opt no-new-privileges`.
- Ha limite de PIDs e tmpfs restrito.
- Montagens de credenciais gerenciadas pelo Hermes sao somente leitura.

## Politica de atualizacao

- Rebuild mensal em ambiente de manutencao.
- Rebuild imediato quando houver CVE relevante em Python, Node, Debian, npm ou
  pacote base instalado.
- Registrar digest da imagem promovida em CI/producao.
- Antes de trocar tags ou bases, rodar:

```bash
source venv/bin/activate
python scripts/check_container_image_policy.py
python -m pytest tests/governanca/test_container_image_policy.py -q
```

## Aprovacao de novas imagens

Novas imagens diretas em arquivos de configuracao, docs operacionais,
Dockerfiles ou defaults de terminal exigem:

- justificativa de origem e mantenedor;
- runtime entregue e versoes alvo;
- estrategia de digest;
- impacto em Docker, Singularity, Modal e Daytona;
- atualizacao de `scripts/check_container_image_policy.py`;
- atualizacao ou nova ADR quando houver impacto arquitetural.

## Pin por digest

Durante desenvolvimento local, tags legiveis sao aceitas. Para CI/producao,
promova a imagem para uma referencia com digest:

```text
ghcr.io/autoarq-paulo/hermes-agent-runtime:python3.11-node20@sha256:<digest>
```

O digest deve ser capturado depois do push ao registry final e tratado como
artefato de release.

Configure o Hermes com digest sem duplicar a imagem:

```bash
export HERMES_TERMINAL_RUNTIME_REPOSITORY=ghcr.io/autoarq-paulo/hermes-agent-runtime
export HERMES_TERMINAL_RUNTIME_TAG=python3.11-node20
export HERMES_TERMINAL_RUNTIME_DIGEST=sha256:<digest>
```

Use `HERMES_TERMINAL_RUNTIME_IMAGE` apenas quando precisar substituir a
referencia completa, por exemplo para desenvolvimento local:

```bash
export HERMES_TERMINAL_RUNTIME_IMAGE=hermes-agent-local:runtime-python3.11-node20
```
