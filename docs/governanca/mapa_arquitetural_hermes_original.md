# Mapa Arquitetural Hermes Original

Documento de governanca para customizacao de fork do Hermes Agent.

Objetivo: servir como base de decisao para extensoes, integracoes e limites de alteracao, com foco em governanca leve e protecao do core.

## Documentos normativos derivados

- `README.md`: porta de entrada da governanca.
- `guardrails_core.md`: regras obrigatorias da Zona A.
- `padroes_de_extensao.md`: padroes para tools, adapters e codigo custom.
- `fluxo_de_atualizacao_upstream.md`: rotina de sincronizacao com upstream.
- `adr/ADR-001-modelo-de-fork.md`: decisao de modelo de fork.
- `adr/ADR-002-protecao-do-core.md`: decisao de blindagem do core.
- `adr/ADR-003-integracao-rm-desacoplada.md`: decisao para TOTVS RM.
- `adr/ADR-004-ambiente-local-wsl2-docker.md`: decisao de ambiente local.

## Premissas de ContextOS Lite

- O core nao deve ser reescrito para acomodar casos locais.
- Extensoes entram pelas bordas: tools registradas, adapters, plugins e dados externos.
- O fluxo principal deve permanecer unidirecional: entrada -> orquestracao -> agente -> tools -> retorno -> persistencia.
- O estado de conversa e o cache de prompt sao contratos, nao detalhes internos.
- Qualquer mudanca que altere formato de prompt, schema de tool, persistencia ou contrato de adapter exige justificativa formal.

## 1. Analise do repositorio

### Entry Points

- `hermes_cli/main.py`: launcher canonico do comando `hermes`. Aplica override de profile antes dos imports, carrega env, monta o parser e despacha subcomandos.
- `cli.py`: entrada da interface interativa. Carrega config, monta o TUI com `prompt_toolkit`, resolve slash commands e instancia o agente.
- `gateway/run.py`: entrada do gateway multiplaforma. Faz bootstrap de env/config, sobe adapters, controla ciclo async e entrega mensagens aos canais.
- `run_agent.py`: entrada standalone do agente. Expõe o loop de conversa com tool calling e tambem pode ser executado diretamente.
- `docker/entrypoint.sh`: bootstrap do container. Copia `.env`, `config.yaml` e `SOUL.md` no volume e executa `hermes`.

### Estrutura funcional observada

- `hermes_cli/`: camada de interface, configuracao, comandos, setup, auth, plugins, skins, profiles, status, gateway e utilitarios de UX.
- `agent/`: suporte interno do agente. Reune construcao de prompt, compressao de contexto, cache de prompt, cliente auxiliar, metadata de modelo, reputacao de uso, memoria e trajetoria.
- `tools/`: capacidades executaveis. Cada tool se registra no `tools.registry` e pode depender de backends locais, containers, browser providers ou APIs externas.
- `gateway/`: orquestracao de mensageria, store de sessoes, status runtime e adapters por plataforma.
- `gateway/platforms/`: contratos e implementacoes especificas por canal.
- `tools/environments/` e `tools/browser_providers/`: backends de runtime para terminal e browser.
- `docker/`: bootstrap e persona padrao do container.

## 2. Mapa arquitetural em camadas

### Entry Points

Arquivos: `hermes_cli/main.py`, `cli.py`, `gateway/run.py`, `run_agent.py`, `docker/entrypoint.sh`.

Responsabilidade: iniciar o sistema, aplicar bootstrap de profile/env/config, escolher o modo de execucao e chamar a camada apropriada.

Fluxo de dados: entrada do usuario ou da plataforma -> bootstrap -> montagem de contexto/config -> criacao do agente ou do gateway -> retorno para a interface.

Dependencias: dependem de configuracao, runtime e core, mas nao devem concentrar logica de negocio. O ponto mais sensivel e `hermes_cli/main.py`, porque ele define `HERMES_HOME` antes dos imports.

### Interface Layer

Arquivos: `cli.py`; `hermes_cli/commands.py`; `hermes_cli/config.py`; `hermes_cli/setup.py`; `hermes_cli/tools_config.py`; `hermes_cli/skills_config.py`; `hermes_cli/model_switch.py`; `hermes_cli/runtime_provider.py`; `hermes_cli/auth.py`; `hermes_cli/providers.py`; `hermes_cli/models.py`; `hermes_cli/status.py`; `hermes_cli/gateway.py`; `hermes_cli/plugins.py`; `hermes_cli/banner.py`; `hermes_cli/callbacks.py`; `hermes_cli/clipboard.py`; `hermes_cli/curses_ui.py`; `hermes_cli/skin_engine.py`; `hermes_cli/skills_hub.py`.

Responsabilidade: expor a experiencia de usuario e os fluxos administrativos. Aqui vivem o parser de comandos, o TUI, a configuracao de modelos/provedores, o setup guiado, o gerenciamento de tools e skills, o status visual e a integracao com plugins.

Fluxo de dados: entrada humana ou de canal -> comandos/config/skills -> resolucao de intencao -> parametros do agente -> execucao do core.

Dependencias: pode chamar o core e os stores, mas nao deve absorver logica de tool execution, schema de sessao ou contrato de adapter. O registry de comandos em `hermes_cli/commands.py` e uma interface publica: ajuda, autocomplete, gateway e menus derivam dele.

### Core Agent Layer

Arquivos: `run_agent.py`; `agent/prompt_builder.py`; `agent/context_compressor.py`; `agent/prompt_caching.py`; `agent/auxiliary_client.py`; `agent/model_metadata.py`; `agent/display.py`; `agent/trajectory.py`; `agent/memory_manager.py`; `agent/usage_pricing.py`; `agent/retry_utils.py`; `agent/subdirectory_hints.py`; `agent/redact.py`; `agent/title_generator.py`.

Responsabilidade: montar o prompt efetivo, manter o cache de prefixo estavel, estimar contexto/custos, executar o loop de tool calling, gerenciar interrupcoes, comprimir contexto, persistir resultado e manter o estado de conversa da sessao.

Fluxo de dados: mensagens de entrada -> system prompt congelado -> chamada ao LLM -> tool calls -> resultados JSON -> novas mensagens -> resposta final -> persistencia.

Dependencias: depende de `model_tools.py`, de stores de estado, de helpers do pacote `agent` e de hooks de plugins. Nao deve depender de UI ou de implementacoes especificas de plataforma.

### Tool Orchestration Layer

Arquivos: `model_tools.py`; `tools/registry.py`; `toolsets.py`; `tools/mcp_tool.py`; `hermes_cli/plugins.py`.

Responsabilidade: descobrir tools, resolver toolsets, filtrar disponibilidade, montar schemas para o modelo e despachar chamadas de funcao com wrappers consistentes.

Fluxo de dados: toolset pedido -> resolucao de nomes -> filtro de disponibilidade -> lista de schemas -> tool call do modelo -> `handle_function_call()` -> `registry.dispatch()` -> JSON de retorno.

Dependencias: orquestra tool modules, plugins e MCP. Nao deve conhecer a UI nem o protocolo de plataforma. O arquivo `tools/registry.py` e o ponto unico de verdade para schema, handler, check_fn e metadados de tool.

Observacao tecnica: `model_tools.get_tool_definitions()` faz post-processamento de schemas para evitar sugestoes invalidas ao modelo, inclusive:

- reescreve o schema de `execute_code` para listar apenas tools sandbox realmente disponiveis;
- remove cross references de browser quando `web_search`/`web_extract` nao estao disponiveis;
- preserva `tool_call` names resolvidos na ultima selecao.

### Capability Layer

Arquivos principais: `tools/web_tools.py`; `tools/file_tools.py`; `tools/terminal_tool.py`; `tools/browser_tool.py`; `tools/code_execution_tool.py`; `tools/delegate_tool.py`; `tools/memory_tool.py`; `tools/todo_tool.py`; `tools/send_message_tool.py`; `tools/session_search_tool.py`; `tools/skills_tool.py`; `tools/skill_manager_tool.py`; `tools/clarify_tool.py`; `tools/homeassistant_tool.py`; `tools/cronjob_tools.py`; `tools/tts_tool.py`; `tools/vision_tools.py`; `tools/image_generation_tool.py`; `tools/rl_training_tool.py`; `tools/transcription_tools.py`; `tools/voice_mode.py`; `tools/process_registry.py`; `tools/managed_tool_gateway.py`; `tools/tool_result_storage.py`; `tools/checkpoint_manager.py`; `tools/approval.py`; `tools/interrupt.py`.

Backends e suporte: `tools/environments/*`; `tools/browser_providers/*`; `tools/browser_camofox.py`; `tools/browser_camofox_state.py`; `tools/tool_backend_helpers.py`; `tools/url_safety.py`; `tools/website_policy.py`; `tools/skills_sync.py`; `tools/skills_guard.py`; `tools/mcp_oauth.py`; `tools/credential_files.py`; `tools/budget_config.py`.

Responsabilidade: implementar uma capacidade por unidade de comportamento, com contrato de entrada/saida em JSON e registro explicito no registry. Estes modulos nao sao o core; sao a superficie executavel.

Fluxo de dados: schema do tool -> handler -> validacoes locais -> chamada ao runtime ou API externa -> JSON serializado.

Dependencias: podem usar config, env e helpers, mas nao devem chamar UI ou gateway diretamente. Quando precisarem de estado persistente, devem usar `get_hermes_home()` e nao caminhos hardcoded.

### State Layer

Arquivos: `hermes_state.py`; `gateway/session.py`; `gateway/status.py`; `tools/memory_tool.py`; `tools/todo_tool.py`; `tools/tool_result_storage.py`; `tools/checkpoint_manager.py`.

Responsabilidade: persistir sessoes, mensagens, titulos, tokens, custos e FTS5; representar a origem da sessao; armazenar status de runtime; manter memoria curada e lista de tarefas do agente.

Fluxo de dados: evento de usuario -> session key / source -> persistencia em SQLite ou arquivo -> recuperacao por resume/search -> reuso em novas chamadas.

Dependencias: usa `HERMES_HOME` como raiz de estado. Nao deve depender do motor de tool execution nem da interface de usuario.

### Runtime Layer

Arquivos: `gateway/platforms/base.py`; `gateway/platforms/*.py`; `gateway/platforms/telegram_network.py`; `gateway/platforms/ADDING_A_PLATFORM.md`; `gateway/config.py`; `gateway/run.py`; `tools/terminal_tool.py`; `tools/environments/*`; `tools/browser_tool.py`; `tools/browser_providers/*`; `docker/entrypoint.sh`; `docker/SOUL.md`.

Responsabilidade: adaptar Hermes ao mundo externo. Aqui ficam os canais de mensageria, o transporte de comandos, o browser e os sandboxs de terminal.

Fluxo de dados: evento externo -> adapter/runtime -> objeto de sessao -> chamada ao agente -> resposta -> delivery pelo mesmo adapter.

Dependencias: dependem de SDKs, credenciais, runtime host e `gateway.status`. O contrato base esta em `gateway/platforms/base.py`; todo novo adapter deve obedecer a ele.

## 3. Fluxo de execucao critico

### Fluxo CLI

1. `hermes_cli/main.py` aplica o profile override antes de importar o resto do sistema.
2. `cli.py` carrega `config.yaml`, `.env`, estado de sessao e comandos.
3. A interface resolve slash commands ou transforma a entrada em mensagem de usuario.
4. `HermesCLI` instancia `AIAgent` com modelo, toolsets, sessao e callbacks.
5. `AIAgent.run_conversation()` monta o system prompt, injeta contexto efemero e chama o LLM.
6. Se o modelo retornar `tool_calls`, `model_tools.handle_function_call()` despacha cada tool pela registry.
7. O resultado JSON volta para o loop, e a mensagem assistente e reavaliada ate sair uma resposta final.
8. A resposta final e impressa no TUI e a sessao e persistida em logs/SQLite.

### Fluxo Gateway

1. `gateway/run.py` faz bootstrap de env/config e sobe os adapters habilitados.
2. O adapter recebe a mensagem externa e cria `SessionSource`/`SessionContext`.
3. O gateway resolve ou reutiliza uma instancia de `AIAgent` por sessao, preservando o system prompt congelado e os schemas de tools.
4. O agente executa o mesmo loop de chamada ao LLM e tool execution usado no CLI.
5. O gateway monitora interrupcoes, aprovacoes, streaming e timeout de inatividade.
6. Ao final, a resposta e reformatada e entregue pelo adapter original.
7. O estado da sessao e atualizado em `gateway.session` e `hermes_state.SessionDB`.

### Pseudofluxo consolidado

```text
Entrada (CLI ou gateway)
  -> bootstrap de profile/env/config
  -> resolucao de comandos / sessao / toolsets
  -> instanciacao de AIAgent
  -> get_tool_definitions()
  -> chamada ao LLM
  -> se houver tool_calls:
       handle_function_call()
       registry.dispatch()
       append tool result
       repetir loop
  -> final_response
  -> persistencia de logs/sessao
  -> entrega da resposta ao canal de origem
```

## 4. Classificacao de zonas de governanca

### Zona A - Nucleo protegido

Arquivos: `run_agent.py`; `model_tools.py`; `tools/registry.py`; `toolsets.py`; `hermes_state.py`; `gateway/run.py`; `gateway/platforms/base.py`; `hermes_cli/main.py`.

Justificativa: estes arquivos definem o contrato central do produto. Eles controlam o loop de agente, o sistema de tools, a taxonomia de capabilities, a persistencia de sessao, o bootstrap do gateway, o contrato base dos adapters e o bootstrap canonico do CLI.

Regra: nao alterar diretamente sem justificativa formal, analise de impacto e teste de regressao. Qualquer mudanca aqui pode quebrar prompt caching, compatibilidade de sessao, disponibilidade de tools ou a integracao multiplaforma.

### Zona B - Cautela

Arquivos: `cli.py`; `hermes_cli/commands.py`; `hermes_cli/config.py`; `hermes_cli/plugins.py`; `hermes_cli/tools_config.py`; `hermes_cli/skills_config.py`; `hermes_cli/model_switch.py`; `hermes_cli/runtime_provider.py`; `hermes_cli/auth.py`; `hermes_cli/setup.py`; `hermes_cli/status.py`; `hermes_cli/gateway.py`; `gateway/session.py`; `gateway/status.py`; `gateway/config.py`; `docker/entrypoint.sh`; `tools/browser_tool.py`; `tools/terminal_tool.py`; `tools/file_tools.py`; `tools/code_execution_tool.py`; `tools/delegate_tool.py`; `tools/send_message_tool.py`; `tools/memory_tool.py`; `tools/todo_tool.py`; `tools/process_registry.py`; `tools/mcp_tool.py`; `tools/skills_tool.py`; `tools/skill_manager_tool.py`; `tools/session_search_tool.py`; `tools/clarify_tool.py`; `tools/homeassistant_tool.py`; `tools/cronjob_tools.py`; `tools/tts_tool.py`; `tools/vision_tools.py`; `tools/image_generation_tool.py`; `tools/rl_training_tool.py`; `tools/web_tools.py`; `tools/transcription_tools.py`; `gateway/platforms/telegram.py`; `gateway/platforms/slack.py`; `gateway/platforms/discord.py`; `gateway/platforms/whatsapp.py`; `gateway/platforms/signal.py`; `gateway/platforms/matrix.py`; `gateway/platforms/mattermost.py`; `gateway/platforms/email.py`; `gateway/platforms/sms.py`; `gateway/platforms/dingtalk.py`; `gateway/platforms/feishu.py`; `gateway/platforms/wecom.py`; `gateway/platforms/homeassistant.py`; `gateway/platforms/webhook.py`; `gateway/platforms/api_server.py`.

Justificativa: sao bordas operacionais. Mudam UX, transportes, integraacoes e comportamento de runtime, mas nao devem alterar o contrato do core sem revisao. Qualquer alteracao aqui precisa considerar compatibilidade com a registry, com o `SessionDB` e com as regras de approvacao/interrupt.

### Zona C - Extensao segura

Arquivos e diretorios: novos arquivos em `tools/` que se registrem na registry; novos adapters em `gateway/platforms/` que herdem `BasePlatformAdapter`; plugins em `~/.hermes/plugins/` ou no escopo de projeto; `docker/SOUL.md`; `gateway/platforms/ADDING_A_PLATFORM.md`; `docs/`; `tests/`; `skills/` e `~/.hermes/skills/`.

Justificativa: sao pontos de extensao natural ja suportados pela arquitetura. Aqui o fork deve preferir adicionar codepaths novos em vez de editar o core.

## 5. Guardrails para blindagem do core

- Nao alterar `run_agent.py` para resolver problema especifico de integracao externa. Se a mudanca for externa, criar tool, adapter ou plugin.
- Nao mudar system prompt, prompt caching ou compressao de contexto no meio da conversa. A unica mutacao aceita de contexto e a compressao controlada pelo core.
- Nao espalhar referencias a tools inexistentes em descricoes de schema. Se houver cross-reference, ela deve ser aplicada dinamicamente em `model_tools.py` apos a verificacao de disponibilidade.
- Nao mudar o schema de `hermes_state.py` sem bump de versao e migracao retrocompativel.
- Nao mudar assinaturas de `BasePlatformAdapter` sem revisar todos os adapters.
- Nao introduzir imports pesados ou eager imports em `tools/__init__.py`.
- Nao hardcodear `~/.hermes` em codigo de estado. Use `get_hermes_home()` para caminho real e `display_hermes_home()` para mensagem ao usuario.
- Nao deixar plugin ou integracao acessar globais do core para patchar comportamento. Plugins devem entrar por hooks, tools ou comandos registrados.

### Quando e permitido alterar

- Quando a mudanca cria um novo ponto de extensao sem tocar no contrato publico existente.
- Quando a mudanca e obrigatoria para compatibilidade de provider, SDK ou plataforma e vem acompanhada de teste.
- Quando a mudanca corrige uma vulnerabilidade, mas mantem o contrato externo.

### Requisitos para alteracao

- ADR obrigatorio para qualquer mudanca em Zona A.
- Analise de impacto em prompt caching, disponibilidade de tools, persistencia de sessao e roteamento do gateway.
- Teste de regressao para o caminho principal afetado.
- Se houver persistencia nova, migracao com compatibilidade para dados existentes.
- Se houver novo canal ou plataforma, smoke test com adapter real ou stub.

## 6. Padrao de extensao (ContextOS Lite)

### Criacao de novas tools

- Criar um arquivo novo em `tools/<nome>_tool.py`.
- Registrar schema, handler, `check_fn` e toolset no `tools.registry`.
- Manter retorno em JSON string.
- Adicionar o import em `model_tools._discover_tools()` se a tool fizer parte do core do fork.
- Incluir a tool no `toolset` apropriado em `toolsets.py` ou registrar via plugin/toolset dinamico.
- Se a tool for especifica do fork, preferir encapsular a logica em um namespace separado e expor apenas um wrapper fino para o registry.

### Criacao de novos adapters

- Implementar uma classe que herde `gateway.platforms.base.BasePlatformAdapter`.
- Manter `connect()`, `disconnect()` e `send()` como contrato minimo.
- Reusar `SessionSource`, `SessionContext` e `gateway.status`.
- Isolar SDKs e credenciais em modulo do adapter, sem trazer dependencia para o core.
- Se houver token unico ou lock compartilhado, usar o padrao de lock scoped de `gateway.status`.

### Organizacao recomendada para o fork

- `custom/`: regras do negocio do fork, prompts derivados, regras internas e glue code.
- `integrations/`: adaptacao para sistemas externos, como ERPs, CRMs, finance, RH ou backends legados.
- `adapters/`: traducoes finas entre contrato Hermes e contrato do sistema externo.
- `fixtures/`: dados de mock, CSV e JSON para validar o fluxo antes da integracao real.
- `tests/`: testes de fronteira, contrato e regressao.

### Como evitar espalhar mudancas pelo core

- Fazer uma unica fronteira de bootstrap para custom code.
- Registrar tudo no registry ou no plugin manager, nunca via import espalhado em varios pontos.
- Nao editar o core para cada novo provider ou sistema legada.
- Manter as transformacoes de dominio na borda da integracao, nao no agente.

## 7. Diretriz para integracao com TOTVS RM

### Posicionamento arquitetural

- RM deve ser tratado como sistema externo.
- O core Hermes nao deve conhecer RM, seus endpoints ou suas entidades.
- A integracao deve entrar como tool ou adapter, nunca como dependencia direta do agente.

### Abordagem recomendada

- Implementar um wrapper de integracao em `integrations/totvs_rm/` ou em `custom/integrations/totvs_rm/`.
- Expor o contrato para o agente como tools claras e limitadas, por exemplo `totvs_rm_query`, `totvs_rm_get_*`, `totvs_rm_list_*` ou uma unica tool com `action` bem definido.
- Usar uma camada de adaptacao que traduza o dominio Hermes para o dominio RM.
- Guardar a logica de autenticacao, paginação, retry e mapping fora de `run_agent.py` e fora do gateway.

### Fase inicial com mock

- Comecar com CSV/JSON como fonte de verdade simulada.
- Emular latencia, erros e formatos de resposta do RM antes de conectar no ambiente real.
- Validar o contrato do agente com dados sinteticos e repetiveis.
- So depois substituir o mock por conectores reais, preservando o mesmo schema de tool.

### Regras de nao acoplamento

- Nao adicionar chamadas RM diretamente em tools genericas.
- Nao misturar regras de negocio RM com regra de prompt do agente.
- Nao usar RM para armazenar estado de sessao Hermes.
- Nao depender de RM para a inicializacao do core.

## 8. Testes arquiteturais

### Validacoes de arquivos criticos

- Teste de snapshot ou contrato para `run_agent.py`, `model_tools.py`, `tools/registry.py`, `toolsets.py`, `hermes_state.py`, `gateway/run.py`, `gateway/platforms/base.py`, `hermes_cli/main.py`, `hermes_cli/commands.py`.
- Validacao automatica de que os imports do core nao passaram a depender de `integrations/totvs_rm` ou de codigo custom sem passagem pela fronteira prevista.

### Protecao contra alteracao do core

- Teste de prompt caching para garantir que o system prompt nao muda entre turnos sem compressao.
- Teste de schema de tools para garantir que nomes e descricoes continuam coerentes.
- Teste de migracao do `SessionDB` para garantir abertura de bases antigas.
- Teste de contract do adapter para garantir que um novo canal implementa `connect/disconnect/send`.

### Validacao de fronteiras

- Teste para garantir que `tools.registry` continua retornando JSON string em erro e sucesso.
- Teste para garantir que `model_tools.get_tool_definitions()` continua filtrando tools por disponibilidade.
- Teste para garantir que `hermes_cli/commands.py` continua alimentando ajuda, autocomplete e dispatch com a mesma fonte.
- Teste para garantir que `gateway/status.py` continua isolando PID, runtime state e scoped locks por `HERMES_HOME`.

### Testes leves sugeridos

- Unit tests com mocks para tools e adapters.
- Smoke tests para CLI e gateway com config minima.
- Boundary tests com AST ou grep para impedir imports proibidos.
- Testes de contrato para `totvs_rm` usando fixtures CSV/JSON.

## 9. Decisoes inferidas do repositorio

- O Hermes foi organizado como sistema dirigido por registry, nao por heranca pesada.
- `tools.registry` e a fonte autoritativa de schemas e handlers.
- `toolsets.py` e politica de capacidade, nao apenas catalogo estatico.
- `run_agent.py` e o coracao do produto; o resto e borda, suporte ou runtime.
- O gateway reusa o mesmo agente e o mesmo loop de tool calling, mudando apenas o canal de entrada/saida.
- Memoria e todo sao estados do agente, nao do canal.
- `gateway.platforms.base.py` define o contrato que todos os adapters devem seguir.
- Plugins sao a extensao oficial para hooks, tools e comandos adicionais.

## 10. Pontos de incerteza

- Plugins e MCP servers sao dinamicos; parte das capabilities reais pode nao aparecer em uma leitura estatica do repositorio.
- Muitos modulos de `hermes_cli/` sao operacionais e podem ser ativados por comando ou plugin, mas nao fazem parte do caminho principal de chat/gateway.
- Alguns adapters de plataforma dependem de SDKs externos e variam conforme credenciais e ambiente.
- O conjunto efetivo de tools habilitadas em tempo de execucao depende de config, env, plugins e disponibilidade de backend.

## 11. Arquivos analisados

### Core e agente

- `run_agent.py`
- `model_tools.py`
- `toolsets.py`
- `tools/registry.py`
- `hermes_state.py`

### Interface e CLI

- `cli.py`
- `hermes_cli/main.py`
- `hermes_cli/commands.py`
- `hermes_cli/config.py`
- `hermes_cli/plugins.py`
- `hermes_cli/tools_config.py`
- `hermes_cli/skills_config.py`
- `hermes_cli/model_switch.py`
- `hermes_cli/runtime_provider.py`
- `hermes_cli/auth.py`
- `hermes_cli/setup.py`
- `hermes_cli/status.py`
- `hermes_cli/gateway.py`
- `hermes_cli/banner.py`
- `hermes_cli/callbacks.py`
- `hermes_cli/clipboard.py`
- `hermes_cli/curses_ui.py`
- `hermes_cli/skin_engine.py`
- `hermes_cli/skills_hub.py`

### Agent support

- `agent/prompt_builder.py`
- `agent/context_compressor.py`
- `agent/prompt_caching.py`
- `agent/auxiliary_client.py`
- `agent/model_metadata.py`
- `agent/display.py`
- `agent/trajectory.py`
- `agent/memory_manager.py`
- `agent/usage_pricing.py`
- `agent/retry_utils.py`
- `agent/subdirectory_hints.py`
- `agent/redact.py`
- `agent/title_generator.py`
- `agent/skill_commands.py`
- `agent/skill_utils.py`
- `agent/smart_model_routing.py`
- `agent/models_dev.py`
- `agent/credential_pool.py`

### Tools e runtime

- `tools/web_tools.py`
- `tools/file_tools.py`
- `tools/terminal_tool.py`
- `tools/browser_tool.py`
- `tools/code_execution_tool.py`
- `tools/delegate_tool.py`
- `tools/memory_tool.py`
- `tools/todo_tool.py`
- `tools/send_message_tool.py`
- `tools/session_search_tool.py`
- `tools/skills_tool.py`
- `tools/skill_manager_tool.py`
- `tools/clarify_tool.py`
- `tools/homeassistant_tool.py`
- `tools/cronjob_tools.py`
- `tools/tts_tool.py`
- `tools/vision_tools.py`
- `tools/image_generation_tool.py`
- `tools/rl_training_tool.py`
- `tools/transcription_tools.py`
- `tools/voice_mode.py`
- `tools/process_registry.py`
- `tools/mcp_tool.py`
- `tools/approval.py`
- `tools/interrupt.py`
- `tools/tool_result_storage.py`
- `tools/checkpoint_manager.py`
- `tools/tool_backend_helpers.py`
- `tools/environments/*`
- `tools/browser_providers/*`

### Gateway e adapters

- `gateway/run.py`
- `gateway/config.py`
- `gateway/session.py`
- `gateway/status.py`
- `gateway/platforms/base.py`
- `gateway/platforms/telegram.py`
- `gateway/platforms/slack.py`
- `gateway/platforms/discord.py`
- `gateway/platforms/whatsapp.py`
- `gateway/platforms/signal.py`
- `gateway/platforms/matrix.py`
- `gateway/platforms/mattermost.py`
- `gateway/platforms/email.py`
- `gateway/platforms/sms.py`
- `gateway/platforms/dingtalk.py`
- `gateway/platforms/feishu.py`
- `gateway/platforms/wecom.py`
- `gateway/platforms/homeassistant.py`
- `gateway/platforms/webhook.py`
- `gateway/platforms/api_server.py`
- `gateway/platforms/telegram_network.py`
- `gateway/platforms/ADDING_A_PLATFORM.md`

### Docker e bootstrap

- `docker/entrypoint.sh`
- `docker/SOUL.md`

## Pontos criticos de observabilidade

- Tempo de execucao de tool.
- Falhas de dispatch de tool.
- Inconsistencia de schema entre registry, toolset e chamada do modelo.
- Divergencia entre CLI e gateway no comportamento de uma mesma acao.
- Erros de persistencia de sessao em SQLite, logs ou recuperacao de conversa.

Esses pontos nao mudam o desenho da arquitetura, mas devem orientar monitoramento futuro, testes de regressao e priorizacao de manutencao.
