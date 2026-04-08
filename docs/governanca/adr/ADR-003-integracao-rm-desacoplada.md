# ADR-003 - Integracao com TOTVS RM Desacoplada

Status: Accepted

## Contexto

TOTVS RM e um sistema externo de negocio. Integracoes desse tipo nao devem entrar no core do Hermes, porque isso aumentaria acoplamento, dificultaria testes e misturaria regras de dominio com o loop do agente.

## Decisao

Integrar RM por meio de tools e adapters fora do core, com camada de traducao de dominio. A primeira iteracao deve usar mock com CSV/JSON para validar contrato, fluxo e mapeamento antes de conectar ao ambiente real.

## Consequencias

- O core permanece agnostico ao RM.
- O contrato de integracao pode ser testado sem acessar sistemas produtivos.
- A evolucao da integracao fica mais segura e mais facil de revisar.
- Pode haver um custo inicial maior de modelagem e mock.

## Alternativas consideradas

- Chamar RM diretamente de `run_agent.py`.
- Misturar regra de RM com tools genericas.
- Integrar RM por acesso direto a banco ou planilha sem camada de adaptacao.

