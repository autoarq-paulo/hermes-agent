# TOTVS RM Mock Extension

## Objetivo

- Validar a estrategia desacoplada de integracao com TOTVS RM sem rede, sem banco real e sem tocar no core.
- A tool `totvs_rm_mock` consulta apenas fixtures JSON locais e devolve o envelope padronizado do fork.

## Actions suportadas

- `listar_coligadas`
- `listar_filiais`
- `listar_funcionarios`
- `listar_movimentos`
- `buscar_coligada_por_codigo`
- `buscar_filial_por_id`
- `buscar_funcionario_por_chapa`
- `buscar_movimento_por_id`

## Retorno enriquecido

- O envelope externo continua com `ok`, `source`, `action`, `data` e `errors`.
- Em sucesso, `data` pode trazer `items`, `item`, `count`, `filters_applied` e `warnings`.
- `fail_on_empty` permite transformar combinacoes vazias em erro funcional previsivel.
- `simulate_error` permite simular `data_unavailable` e `inconsistent_record` sem criar infraestrutura real.

## Estrutura

- `integrations/totvs_rm/mock_loader.py` le os dados locais.
- `integrations/totvs_rm/mock_service.py` implementa a logica de dominio e filtros.
- `adapters/totvs_rm/response_adapter.py` monta o envelope final.
- `tools/totvs_rm_mock_tool.py` segue como borda fina, sem registro automatico.
- O plugin de projeto `.hermes/plugins/totvs_rm/` faz o registro no Hermes quando `HERMES_ENABLE_PROJECT_PLUGINS=true`.

## Valor arquitetural

- Mantem RM fora de `run_agent.py` e fora do motor central.
- Mantem a extensao previsivel, local e substituivel.
- Aumenta o realismo do mock sem acoplar rede, banco ou integracao real.

## Excecao controlada

- A tool continua fora do discovery do core.
- O plugin de projeto preserva o desacoplamento do core e evita reestruturar `model_tools.py`.
