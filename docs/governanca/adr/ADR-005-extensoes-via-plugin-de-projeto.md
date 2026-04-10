# ADR-005 - Extensoes via Plugin de Projeto

Status: Accepted

## Contexto

O fork evoluiu de uma tentativa de discovery custom em `model_tools.py` e de um helper de discovery anterior para carregar extensoes de dominio. Essa abordagem funcionou como transicao, mas aumentou a superficie de merge com o upstream, criou dependencia de bootstrap central e misturou a fronteira do core com a carga de integracoes do fork.

A integracao TOTVS RM foi depois movida para `.hermes/plugins/totvs_rm/`, com `plugin.yaml` e um `register(ctx)` explicito. Esse movimento mostrou que o problema era de fronteira de integracao, nao de engine.

## Decisao

Adotar plugins de projeto como padrao arquitetural para extensoes de dominio do fork. Toda nova integracao de dominio deve viver em `.hermes/plugins/<nome>/`, declarar seu manifesto em `plugin.yaml` e registrar tools pelo entrypoint do plugin. O core Hermes nao deve receber discovery custom, auto-registro por import ou alteracoes permanentes em `model_tools.py` para atender extensoes do fork.

## Consequencias

- O core permanece alinhado ao upstream e com menor superficie de conflito.
- A integracao do fork fica isolada na fronteira do plugin.
- A ativacao passa a ser explicita por `HERMES_ENABLE_PROJECT_PLUGINS=true`.
- Testes e execucoes que precisam de core limpo podem manter o plugin desligado.
- O contrato de extensao fica mais facil de revisar, isolar e remover.

## Trade-offs

- O carregamento deixa de ser automatico em todo contexto.
- Quem precisa da extensao deve ativar o plugin de projeto de forma consciente.
- Ha um artefato a mais para manter (`plugin.yaml` + entrypoint), mas ele substitui alteracoes recorrentes no core.
- Falhas de plugin aparecem na borda de carga, nao espalhadas pelo bootstrap central.

## Diretrizes

- Novas extensoes de dominio do fork devem preferir plugins de projeto.
- Nao reintroduzir discovery custom em `model_tools.py` para extensoes do fork.
- Nao depender de auto-registro implicito em wrappers de `tools/`.
- Tratar plugins como fronteira de integracao; o core so deve conhecer capacidades basicas e estaveis.
- Se uma mudanca exigir tocar no core para carregar uma extensao, abrir ADR especifico antes de alterar o design.

## Alternativas consideradas

- Manter discovery custom no core.
- Voltar ao auto-registro por import em wrappers.
- Centralizar o carregamento em `run_agent.py`.
