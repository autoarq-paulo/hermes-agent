# ADR-006 - Runtime container supply chain

Status: Accepted

Atualizacao: a publicacao em registry, estrategia de tags GHCR e uso por digest
foram fechados na [ADR-007](./ADR-007-publicacao-runtime-ghcr.md).

## Contexto

O Hermes executa comandos em backends locais e remotos como Docker,
Singularity/Apptainer, Modal e Daytona. O fork usava defaults e exemplos com a
imagem externa `nikolaik/python-nodejs:python3.11-nodejs20`, funcional, mas
mantida fora de uma origem oficial ou controlada pelo projeto.

O fork tambem precisa preservar compatibilidade com upstream: o core deve
continuar aceitando overrides por configuracao e variaveis `TERMINAL_*_IMAGE`.

## Problema

A imagem antiga combina Python e Node, mas cria risco de supply chain por:

- depender de mantenor externo nao oficial;
- usar tag mutavel sem digest;
- aparecer em varios pontos de configuracao e documentacao;
- nao ter politica local explicita para aprovacao de novas imagens.

## Decisao

Criar uma imagem de runtime propria do fork em
`docker/Dockerfile.runtime-python-node`, baseada em imagens oficiais:

- `python:3.11-slim-bookworm`;
- `node:20-bookworm-slim` como estagio fonte para Node.js 20.

Na primeira etapa, o runtime local aprovado passou a ser
`hermes-agent-local:runtime-python3.11-node20`, definido em `hermes_constants.py`
e consumido pelos defaults de Docker, Singularity, Modal e Daytona. Os backends
continuam aceitando overrides por config/env. Para Modal e Daytona, a mesma
imagem deve ser publicada em um registry antes do uso, porque esses provedores
nao conseguem consumir uma tag local do Docker daemon.

## Alternativas consideradas

- Manter `nikolaik/python-nodejs`: menor esforco, mas preserva a dependencia de
  terceiro nao oficial e tag mutavel.
- Usar apenas `python:3.11-slim-bookworm`: origem oficial, mas quebra fluxos que
  dependem de Node.js.
- Usar uma imagem devcontainer pronta: reduz trabalho, mas troca uma dependencia
  externa por outra imagem agregada e menos especifica ao contrato do Hermes.
- Alterar profundamente o Docker backend para usuario nao-root: melhora
  isolamento, mas conflita com o contrato atual de `/root`, persistencia e
  instalacao sob demanda por `apt`, `pip` e `npm`.

## Tradeoffs

- A imagem propria aumenta manutencao local, mas torna o runtime auditavel.
- O Dockerfile usa tags oficiais sem digest para facilitar rebuild local; a
  politica exige pin por digest na promocao para CI/producao.
- O container ainda inicia como root para compatibilidade. A mitigacao atual e
  a hardening ja aplicada pelo `DockerEnvironment`: `cap-drop ALL`,
  `no-new-privileges`, limites de PID e tmpfs restrito.
- Modal e Daytona precisam de publicacao previa da imagem em registry confiavel.

## Riscos aceitos

- Tags oficiais continuam mutaveis ate que a imagem seja promovida com digest.
- O usuario root dentro do container permanece aceito no curto prazo por
  compatibilidade operacional.
- O registry final para Modal/Daytona ainda e uma decisao de ambiente.

## Impacto em fork/upstream

A mudanca toca minimamente o core: apenas a centralizacao de defaults em
`hermes_constants.py` e consumidores de configuracao existentes. A imagem, docs
e guardrails ficam em camadas locais de infra/governanca. Em merges futuros do
upstream, conflitos provaveis estao restritos a defaults de terminal e docs.

## Manutencao futura

- Rebuild mensal ou quando houver CVE relevante em Python, Node, Debian, npm ou
  ferramentas basicas instaladas.
- Promover tags operacionais com digest registrado em ambiente/CI.
- Rodar `python scripts/check_container_image_policy.py` antes de merge.
- Atualizar `docs/governanca/runtime_container_policy.md` antes de aprovar nova
  imagem direta em configuracao, docs operacionais ou Dockerfiles.
