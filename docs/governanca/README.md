# Governanca do Fork Hermes Agent

Este diretorio concentra a governanca leve do fork.

## Proposito

- Definir limites claros para customizacao do fork.
- Proteger o core contra alteracoes acidentais.
- Padronizar extensoes, integracoes e atualizacoes de upstream.
- Registrar decisoes arquiteturais para evitar divergencia silenciosa.

## Como usar

1. Leia este README para entender a estrutura.
2. Leia o mapa arquitetural para ver a topologia real do repositorio.
3. Leia os guardrails do core antes de alterar qualquer arquivo da Zona A.
4. Leia os padroes de extensao antes de criar tools, adapters ou integracoes.
5. Leia o fluxo de upstream antes de sincronizar com a origem.
6. Leia os ADRs quando a mudanca tocar em fork, core, RM ou ambiente local.

## Distincao entre documentos

- Mapa arquitetural: descreve a estrutura real do repositorio e os fluxos principais.
- Guardrails: define regras obrigatorias e limites de alteracao.
- Padroes de extensao: explica como adicionar capacidade sem acoplar ao core.
- Fluxo de atualizacao upstream: define a rotina operacional de sincronizacao com a origem.
- ADRs: registram decisoes arquiteturais com contexto, decisao e consequencias.

## Regras basicas do fork

- `main` deve permanecer limpa e o mais proxima possivel do `upstream/main`.
- Customizacoes devem entrar por tools, adapters, plugins ou codigo custom fora do core.
- Qualquer mudanca na Zona A exige ADR, analise de impacto e teste.
- Integracoes externas, incluindo TOTVS RM, nao devem ser acopladas ao core.
- O uso de mock com CSV/JSON e a primeira etapa padrao para novas integracoes.
- Mudancas que alterem prompt, schema de tool, persistencia ou contrato de adapter sao mudancas arquiteturais, nao ajustes pontuais.

## Estrutura de leitura recomendada

- [mapa_arquitetural_hermes_original.md](./mapa_arquitetural_hermes_original.md)
- [guardrails_core.md](./guardrails_core.md)
- [padroes_de_extensao.md](./padroes_de_extensao.md)
- [fluxo_de_atualizacao_upstream.md](./fluxo_de_atualizacao_upstream.md)
- [adr/ADR-001-modelo-de-fork.md](./adr/ADR-001-modelo-de-fork.md)
- [adr/ADR-002-protecao-do-core.md](./adr/ADR-002-protecao-do-core.md)
- [adr/ADR-003-integracao-rm-desacoplada.md](./adr/ADR-003-integracao-rm-desacoplada.md)
- [adr/ADR-004-ambiente-local-wsl2-docker.md](./adr/ADR-004-ambiente-local-wsl2-docker.md)

## Termos usados

- Zona A: nucleo protegido.
- Zona B: cautela.
- Zona C: extensao segura.
- Core: conjunto de arquivos que definem contrato, loop e persistencia central.
- Upstream: origem oficial do projeto.
- RM: TOTVS RM, tratado como sistema externo.

## O que este pacote NÃO cobre

- Implementacao de features de produto.
- Detalhes internos de ferramentas especificas.
- Decisoes operacionais locais que nao alterem o contrato do fork.
- Experimentos de curto prazo que nao pretendam virar padrao.
