# Guardrails do Core

## Objetivo

Definir as regras obrigatorias para proteger a Zona A do fork Hermes Agent. Estas regras existem para evitar que customizacoes locais quebrem o loop do agente, o cache de prompt, a persistencia de sessao, o sistema de tools ou o gateway multiplaforma.

## Zona A

A Zona A corresponde ao nucleo protegido descrito no mapa arquitetural. Os arquivos principais sao:

- `run_agent.py`
- `model_tools.py`
- `tools/registry.py`
- `toolsets.py`
- `hermes_state.py`
- `gateway/run.py`
- `gateway/platforms/base.py`
- `hermes_cli/main.py`

## Regras nao negociaveis

- Nao alterar o loop principal do agente para acomodar integracoes externas.
- Nao alterar o system prompt, o cache de prompt ou a estrategia de compressao no meio da conversa.
- Nao acoplar sistemas externos diretamente ao core.
- Nao mudar contratos de tool, schema de sessao ou assinatura base de adapter sem revisao formal.
- Nao introduzir dependencias de UI, gateway ou runtime especifico dentro do motor do agente.
- Nao hardcodear caminhos de estado fora de `get_hermes_home()`.

## Quando e permitido alterar o core

- Quando a mudanca corrige bug estrutural no caminho principal.
- Quando a mudanca e necessaria para compatibilidade com SDK, provider ou plataforma e nao existe alternativa por extensao.
- Quando a mudanca preserva o contrato externo e e acompanhada de teste e analise de impacto.
- Quando a mudanca tem ADR aprovado e plano de rollback.

## Requisitos obrigatorios

- ADR obrigatorio para qualquer mudanca na Zona A.
- Analise de impacto em prompt caching, disponibilidade de tools, persistencia e roteamento do gateway.
- Teste de regressao para o caminho afetado.
- Se houver persistencia nova, migracao retrocompativel.
- Se houver mudanca de adapter, validação com o contrato base.

## Exemplos de violacao

- Colocar logica de TOTVS RM diretamente em `run_agent.py`.
- Mudar a estrutura do `SessionDB` sem migracao.
- Adicionar cross references fixas em schemas de tools que podem nao estar disponiveis.
- Alterar o bootstrap canonico do CLI para resolver um caso de integracao.
- Criar acoplamento direto entre adapter de plataforma e estado interno do agente.

## Impacto de quebra

- Quebra de prompt caching.
- Perda de compatibilidade de sessoes salvas.
- Tool calls invalidas ou indisponiveis.
- Erros de gateway em tempo de execucao.
- Divergencia entre CLI, gateway e batch runner.
- Maior custo de manutencao e maior risco de regressao em futuras atualizacoes de upstream.

## Reforco automatizavel (preparacao para CI)

- Validar alteracoes nos arquivos da Zona A sempre que houver diff em `run_agent.py`, `model_tools.py` ou `tools/registry.py`.
- Tratar mudancas nesses arquivos como candidatas a bloqueio ate existir ADR correspondente.
- Usar uma verificacao simples por `diff`, `grep` ou `AST` para identificar alteracoes estruturais antes do merge.
- Sinalizar quando o PR tocar em Zona A sem referencia explicita ao ADR de origem ou sem justificativa formal.
- Manter essa checagem como preparacao para enforcement futuro, sem codificar a regra no documento como implementacao de CI.
