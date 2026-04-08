# ADR-004 - Ambiente Local WSL2 + Docker

Status: Accepted

## Contexto

O fork precisa de um ambiente local previsivel para desenvolvimento, testes e validacao de integracoes externas. O repositorio ja possui suporte a Docker e o ecossistema Hermes e sensivel a diferencas de plataforma, caminhos e isolamento de runtime.

## Decisao

Padronizar o ambiente local em WSL2 para desenvolvimento no Windows e Docker para isolamento de runtime. Dados usados em desenvolvimento e validacao devem ser ficticios ou mockados, e o RM deve permanecer isolado do core e do ambiente local por padrao.

## Consequencias

- Reduz diferencas entre ambiente local e ambiente de execucao.
- Facilita isolamento de credenciais, arquivos e processos.
- Permite validar integracoes sem expor sistemas reais.
- Exige disciplina para manter dados de teste ficticios e contrato de mock consistente.

## Alternativas consideradas

- Desenvolvimento nativo em Windows sem camada Linux.
- Execucao direta no host sem isolamento de container.
- Acesso direto ao RM a partir do ambiente local de desenvolvimento.
