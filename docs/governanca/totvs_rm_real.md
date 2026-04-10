# TOTVS RM Real Integration Fase 2

## Objetivo

- Evoluir a base controlada da integracao real sem substituir o mock nem tocar no core.
- A fase 2 amplia o realismo do transporte por action e adiciona duas actions preparatorias.

## Diferenca para o mock

- O mock usa fixtures locais e cobre cenarios governados de dominio.
- A integracao real continua sem fallback para o mock e nao assume rede real no teste.
- O mock permanece como ferramenta de previsibilidade e regressao.

## Estrutura

- `integrations/totvs_rm/real_client.py` encapsula configuracao, transporte e metadados por action.
- `integrations/totvs_rm/real_service.py` normaliza `action + payload` para o contrato do fork.
- `adapters/totvs_rm/real_response_adapter.py` preserva o envelope externo `ok/source/action/data/errors`.
- O fallback `mock://totvs-rm/...` no client e tecnico e transitorio: facilita foundation e teste, nao representa endpoint real nem contrato final.

## Exposicao ao agente

- A tool real e `totvs_rm_real`, registrada pelo plugin de projeto `.hermes/plugins/totvs_rm/` quando `HERMES_ENABLE_PROJECT_PLUGINS=true`.
- A tool mock continua separada como `totvs_rm_mock`.
- O plugin de projeto e o ponto unico de entrada da integracao; wrappers em `tools/` nao se auto-registram.
- A ativacao depende do ambiente, nao de alteracao no core nem de discovery custom.
- Nao existe fallback implicito entre as duas tools.
- Se a configuracao real nao existir, a tool real retorna erro controlado no envelope padronizado.

## Limites desta fase

- Estao preparados `buscar_funcionario_por_chapa`, `buscar_movimento_por_id`, `buscar_filial_por_id` e `buscar_coligada_por_codigo`.
- O client agora diferencia rota, metodo e headers por action, mas ainda usa transporte injetavel nos testes.
- A tool real foi mantida fora do discovery do core e entra apenas pelo plugin de projeto.
- A integracao nao depende mais do discovery custom anterior nem de alteracoes em `model_tools.py`.
- Nao ha rede real obrigatoria nem banco de producao.
- A evolucao futura pode ampliar o client e o service sem reestruturar o fork.
