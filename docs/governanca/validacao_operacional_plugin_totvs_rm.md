# Validacao Operacional do Plugin de Projeto TOTVS RM

## Objetivo

Validar localmente, de forma controlada, que o plugin de projeto TOTVS RM funciona como esperado sem alterar arquitetura nem comportamento funcional.

## Cenarios validados

### Cenario A - execucao limpa sem plugin

- Ambiente: `HERMES_HOME=$(mktemp -d)` e `HERMES_ENABLE_PROJECT_PLUGINS` ausente.
- Validacao:
  - `hermes tools list --platform cli`
  - inspecao direta com `PluginManager().discover_and_load()`
- Resultado:
  - o core carregou apenas toolsets built-in.
  - `totvs_rm_mock` e `totvs_rm_real` nao apareceram.
  - `registry.get_toolset_for_tool("totvs_rm_mock")` e `registry.get_toolset_for_tool("totvs_rm_real")` retornaram `null`.
  - aprovado.

### Cenario B - execucao com plugin habilitado

- Ambiente: `HERMES_HOME=$(mktemp -d)` e `HERMES_ENABLE_PROJECT_PLUGINS=true`.
- Validacao:
  - `hermes tools list --platform cli`
  - inspecao direta com `PluginManager().discover_and_load()`
- Resultado:
  - o plugin `totvs_rm` foi carregado.
  - `totvs_rm_mock` e `totvs_rm_real` apareceram como plugin toolsets.
  - ambas coexistiram sem colisao.
  - aprovado.

### Cenario C - uso controlado do mock

- Ambiente: `HERMES_HOME=$(mktemp -d)` e `HERMES_ENABLE_PROJECT_PLUGINS=true`.
- Validacao:
  - `PluginManager().discover_and_load()`
  - `registry.dispatch("totvs_rm_mock", {"action": "buscar_funcionario_por_chapa", "payload": {"chapa": "000123"}})`
  - `registry.dispatch("totvs_rm_mock", {"action": "acao_inexistente", "payload": {}})`
- Resultado:
  - resposta valida preservou o contrato JSON com `ok`, `source`, `action`, `data` e `errors`.
  - resposta invalida foi previsivel e controlada.
  - aprovado.

### Cenario D - uso controlado da real sem configuracao adequada

- Ambiente: `HERMES_HOME=$(mktemp -d)`, `HERMES_ENABLE_PROJECT_PLUGINS=true` e variaveis `TOTVS_RM_REAL_*` removidas do ambiente.
- Validacao:
  - `PluginManager().discover_and_load()`
  - `registry.dispatch("totvs_rm_real", {"action": "buscar_coligada_por_codigo", "payload": {"codigo": "COL001"}})`
- Resultado:
  - a tool real nao caiu para o mock.
  - a resposta foi um erro previsivel e controlado.
  - o erro deixou explicita a ausencia de configuracao: `base_url e obrigatorio quando transport nao e informado`.
  - aprovado.

## Comandos executados

```bash
HERMES_HOME=$(mktemp -d) env -u HERMES_ENABLE_PROJECT_PLUGINS python3 -m hermes_cli.main tools list --platform cli
HERMES_HOME=$(mktemp -d) HERMES_ENABLE_PROJECT_PLUGINS=true python3 -m hermes_cli.main tools list --platform cli
HERMES_HOME=$(mktemp -d) env -u HERMES_ENABLE_PROJECT_PLUGINS python3 - <<'PY'
from hermes_cli.plugins import PluginManager
from tools.registry import registry

mgr = PluginManager()
mgr.discover_and_load()
assert "totvs_rm" not in mgr._plugins
assert registry.get_toolset_for_tool("totvs_rm_mock") is None
assert registry.get_toolset_for_tool("totvs_rm_real") is None
PY
HERMES_HOME=$(mktemp -d) HERMES_ENABLE_PROJECT_PLUGINS=true python3 - <<'PY'
import json
import os
from hermes_cli.plugins import PluginManager
from tools.registry import registry

for key in [
    "TOTVS_RM_REAL_BASE_URL",
    "TOTVS_RM_REAL_USERNAME",
    "TOTVS_RM_REAL_PASSWORD",
    "TOTVS_RM_REAL_TOKEN",
    "TOTVS_RM_REAL_TIMEOUT_SECONDS",
]:
    os.environ.pop(key, None)

mgr = PluginManager()
mgr.discover_and_load()
assert {"totvs_rm_mock", "totvs_rm_real"} <= mgr._plugin_tool_names
json.loads(registry.dispatch("totvs_rm_mock", {"action": "buscar_funcionario_por_chapa", "payload": {"chapa": "000123"}}))
json.loads(registry.dispatch("totvs_rm_mock", {"action": "acao_inexistente", "payload": {}}))
json.loads(registry.dispatch("totvs_rm_real", {"action": "buscar_coligada_por_codigo", "payload": {"codigo": "COL001"}}))
PY
```

## Resultados

- Cenario A: aprovado.
- Cenario B: aprovado.
- Cenario C: aprovado.
- Cenario D: aprovado.

## Problemas encontrados

- Nenhum problema funcional no plugin ou no core.
- O ambiente local nao tinha `venv/` na raiz, entao a validacao usou `python3` do ambiente disponivel.

## Conclusao operacional

O plugin de projeto TOTVS RM esta operacional:

- sem `HERMES_ENABLE_PROJECT_PLUGINS=true`, o core permanece limpo;
- com a variavel habilitada, `totvs_rm_mock` e `totvs_rm_real` aparecem explicitamente;
- o mock responde com contrato JSON previsivel;
- a integracao real falha de forma controlada quando a configuracao nao esta pronta;
- nao existe fallback silencioso para o mock;
- nao houve necessidade de tocar no core.
