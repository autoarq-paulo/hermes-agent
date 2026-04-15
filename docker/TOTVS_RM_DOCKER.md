# Docker Desktop com plugin TOTVS RM

Este projeto ja tem o plugin de projeto TOTVS RM em:

```text
.hermes/plugins/totvs_rm
```

Ele registra as tools `totvs_rm_mock` e `totvs_rm_real`, e so e carregado quando:

```text
HERMES_ENABLE_PROJECT_PLUGINS=true
```

O `docker-compose.yml` da raiz ja sobe o Hermes com essa variavel ativa.

Para o backend Docker do tool `terminal`, o fork agora usa por padrao a imagem
local construida por este repositorio:

```text
hermes-agent-local:rm-adapter
```

Isso evita depender da imagem externa upstream quando o agente abre um sandbox
Docker para executar comandos. Se quiser trocar o tag local, ajuste:

```text
TERMINAL_DOCKER_IMAGE
```

ou:

```text
HERMES_LOCAL_DOCKER_IMAGE
```

## O que entra no container

- codigo da branch atual via `docker build` local
- estado persistente em `./docker/data`
- plugin de projeto montado em `./.hermes/plugins`

Persistencia de banco SQLite:

- o container usa `HERMES_HOME=/opt/data`
- qualquer estado duravel deve ficar em `./docker/data`
- por compatibilidade, `usage_logging.db` acessado como `/opt/hermes/usage_logging.db`
  e redirecionado no entrypoint para `/opt/data/usage_logging.db`

Importante:

- se voce alterar Python, tools, adapters, integrations ou fixtures fora de `./.hermes/plugins`, rode novo `docker compose build`
- se voce alterar apenas o plugin em `./.hermes/plugins`, basta reiniciar o container

## Primeira execucao

Crie a pasta de dados:

```bash
mkdir -p docker/data
```

Build da imagem com suas customizacoes atuais:

```bash
docker compose build
```

Em ambientes com inspeção TLS no gateway, como Sophos XG Home Edition, a imagem usa
o certificado exportado em:

```text
docker/certs/sophos-xg-home.crt
```

Esse CA e aplicado durante a build para que `pip`, `npm` e o restante da imagem
consigam usar o trust store correto depois do bootstrap inicial do Debian.

Bootstrap inicial do Hermes:

```bash
docker compose run --rm --profile cli hermes-cli setup
```

Isso cria os arquivos base em `docker/data/`, incluindo `.env` e `config.yaml`.

## Rodando no Docker Desktop

CLI interativo:

```bash
docker compose run --rm --profile cli hermes-cli
```

Gateway em background:

```bash
docker compose --profile gateway up -d hermes-gateway
```

Logs do gateway:

```bash
docker compose logs -f hermes-gateway
```

Parar:

```bash
docker compose --profile gateway down
```

## TOTVS RM mock

O mock usa fixtures locais de:

```text
fixtures/totvs_rm/
```

Como essas fixtures vao na imagem durante o build, o fluxo recomendado e:

```bash
docker compose build
docker compose run --rm --profile cli hermes-cli
```

Se voce alterar arquivos em `fixtures/totvs_rm/`, `integrations/totvs_rm/`, `tools/totvs_rm_*` ou `adapters/totvs_rm/`, faca build de novo.

## TOTVS RM real

A integracao real depende destas variaveis no ambiente do Hermes:

```text
TOTVS_RM_REAL_BASE_URL
TOTVS_RM_REAL_USERNAME
TOTVS_RM_REAL_PASSWORD
TOTVS_RM_REAL_TOKEN
TOTVS_RM_REAL_TIMEOUT_SECONDS
```

Coloque essas variaveis em:

```text
docker/data/.env
```

Exemplo:

```dotenv
TOTVS_RM_REAL_BASE_URL=https://seu-rm.exemplo/api
TOTVS_RM_REAL_USERNAME=usuario
TOTVS_RM_REAL_PASSWORD=senha
TOTVS_RM_REAL_TIMEOUT_SECONDS=15
```

Se voce usa token bearer em vez de basic auth:

```dotenv
TOTVS_RM_REAL_BASE_URL=https://seu-rm.exemplo/api
TOTVS_RM_REAL_TOKEN=seu-token
TOTVS_RM_REAL_TIMEOUT_SECONDS=15
```

## Validacao rapida

Listar tools com plugin habilitado:

```bash
docker compose run --rm --profile cli hermes-cli tools list --platform cli
```

Voce deve ver `totvs_rm_mock` e `totvs_rm_real`.

## Fluxo recomendado para desenvolvimento

1. Ajuste o codigo na branch `paulo/rm-adapter`
2. Rode `docker compose build`
3. Suba com `docker compose run --rm --profile cli hermes-cli`
4. Se mexer so em `./.hermes/plugins`, reinicie sem rebuild

Observacao:

- a primeira build pode demorar bastante porque instala dependencias grandes como Node, ffmpeg e o stack usado pelo Playwright
