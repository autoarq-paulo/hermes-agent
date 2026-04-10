# Ativacao de Plugins de Projeto

## Objetivo

Documentar quando e como habilitar plugins de projeto do fork, incluindo a integracao TOTVS RM.

## Como ativar

```bash
export HERMES_ENABLE_PROJECT_PLUGINS=true
```

Com a variavel ligada, o gerenciador de plugins do Hermes considera os manifests em `.hermes/plugins/` e carrega os plugins declarados por `plugin.yaml`.

## Quando ativar

- Desenvolvimento local de extensoes de dominio.
- Homologacao e validacao funcional do fork.
- Testes que precisam da integracao do fork carregada.

## Quando nao ativar

- Execucao limpa do core.
- Testes isolados de componentes que nao devem ver extensoes do fork.
- Validacao de compatibilidade com upstream sem o delta do plugin.

## Regra operacional

- A ausencia da variavel deve ser tratada como comportamento esperado, nao como erro.
- O plugin de TOTVS RM e outras extensoes do fork nao devem assumir carga automatica.
- Se o contexto precisar da extensao, a ativacao deve ser explicita.
