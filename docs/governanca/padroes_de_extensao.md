# Padroes de Extensao

## Objetivo

Definir como estender o fork sem acoplar ao core. O principio e simples: se a capacidade e nova ou externa, ela entra pela borda, nao pelo nucleo.

## Onde criar tools

- Criar novas tools em `tools/<nome>_tool.py`.
- Registrar schema, handler e disponibilidade em `tools/registry.py`.
- Incluir o modulo em `custom/tool_discovery.py` quando a tool for extensao do fork.
- Manter `model_tools.CORE_TOOL_MODULES` como baseline fixo do Hermes e importar o ponto de extensao do fork logo depois.
- Manter a resposta da tool em JSON string.
- Se a tool for especifica do fork, isolar a logica em modulo proprio e expor apenas um wrapper fino para o registry.

## Onde criar adapters

- Para integracoes de mensageria, usar `gateway/platforms/` e herdar `BasePlatformAdapter`.
- Para sistemas externos de negocio, usar uma area de integracao fora do core, como `integrations/` com adaptadores finos em `adapters/`.
- Para integracoes de dominio do fork, manter a traducao entre o dominio Hermes e o dominio externo em um modulo separado da regra do agente.

## Estrutura sugerida para o fork

- `custom/`: regras e glue code especificos do fork.
- `integrations/`: conectores para sistemas externos.
- `adapters/`: traducao fina entre Hermes e sistemas externos.
- `fixtures/`: CSV e JSON de mock para validacao inicial.

## Como evitar acoplamento ao core

- Nao editar `run_agent.py` para cada nova integracao.
- Nao espalhar importacoes de integracao em varios pontos do core.
- Nao modificar o system prompt para carregar regra de negocio externa.
- Nao chamar sistemas externos a partir de tools genericas sem uma camada de adaptacao.
- Nao usar estado global do core como transporte de dados da integracao.

## Decisoes transitorias e fallback tecnico

- Qualquer fallback tecnico, workaround, compatibilidade temporaria ou placeholder que possa parecer definitivo deve receber comentario explicito de intencao no codigo.
- Se a decisao afetar arquitetura ou contrato publico, documentar tambem em `docs/governanca/`.
- O comentario deve deixar claro o limite da decisao e o que nao deve ser propagado sem revisao.
- Isso evita que uma mitigacao local seja confundida com o padrao do fork.

## Boas praticas

- Manter uma responsabilidade por modulo.
- Registrar tudo pelo mecanismo oficial de registry ou plugins.
- Usar `get_hermes_home()` para estado persistente.
- Fazer mock primeiro com CSV/JSON antes de trocar pela integracao real.
- Preservar compatibilidade de schema e contratos publicos.
- Preferir wrappers pequenos e teste de contrato em torno deles.

## Anti-patterns

- Colocar regra de RM dentro de tool generica de arquivo, terminal ou browser.
- Alterar o core para "resolver logo" um caso de negocio externo.
- Criar dependencias circulares entre adapters e agente.
- Usar `~/.hermes` hardcoded em nova persistencia.
- Acoplar integracao externa ao cache de prompt ou ao sistema de memoria do agente.

## Regra de decisao rapida

Pergunta: "Isso precisa existir no core?"

- "nao tenho certeza" -> NAO vai para o core.
- "talvez" -> NAO vai para o core.
- "sim, estrutural e inevitavel" -> avaliar ADR antes de tocar no core.

Essa regra existe para reduzir decisoes erradas no dia a dia e manter o fork consistente com a ideia de governanca leve.
