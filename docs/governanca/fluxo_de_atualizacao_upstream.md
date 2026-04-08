# Fluxo de Atualizacao Upstream

## Objetivo

Manter o fork alinhado ao repositorio original sem misturar customizacoes locais no `main`.

## Premissa operacional

- `main` deve acompanhar o `upstream/main`.
- Customizacoes devem viver em branches de adaptacao ou em codigo isolado fora do core.
- A atualizacao de upstream nao deve ser feita sobre um worktree sujo.

## Verificacao antes do update

```bash
git status
git diff --stat
```

Regra:

- se houver mudancas locais, NAO atualizar upstream;
- garantir working tree limpa antes do pull.

## Passo a passo

### 1. Conferir remotos

```bash
git remote -v
```

Se o remoto `upstream` ainda nao existir:

```bash
git remote add upstream <URL_DO_REPOSITORIO_ORIGINAL>
git remote -v
```

### 2. Buscar atualizacoes

```bash
git fetch upstream --prune
```

### 3. Atualizar a branch limpa de base

```bash
git switch main
git pull --ff-only upstream main
```

Se o `--ff-only` falhar, a branch local deixou de ser limpa. Nesse caso:

- mova os commits locais para uma branch de adaptacao;
- nao misture customizacoes com o baseline;
- resolva a divergencia antes de continuar.

### 4. Rebase ou merge da branch de adaptacao

Para branches do fork:

```bash
git switch <sua-branch>
git rebase main
```

Se o fluxo do time preferir merge em vez de rebase:

```bash
git switch <sua-branch>
git merge main
```

### 5. Validacao pos-update

```bash
python -m pytest tests/test_model_tools.py -q
python -m pytest tests/test_cli_init.py -q
python -m pytest tests/gateway/ -q
python -m pytest tests/tools/ -q
```

Quando houver mudanca sensivel no core:

```bash
python -m pytest tests/ -q
```

### 6. Verificacao de impacto

```bash
git status --short
git log --oneline --graph --decorate --all -n 20
```

## Erros comuns

- Atualizar `main` com commits de customizacao misturados.
- Ignorar conflitos em Zona A sem ADR.
- Nao rodar testes apos pull do upstream.
- Reintroduzir imports ou contratos antigos que o upstream removeu.
- Misturar migracao de configuracao com ajuste de integracao externa.

## Rollback

Se a atualizacao trouxer regressao:

```bash
git reflog
git branch rescue/pre-update <SHA_ANTERIOR_BOM>
git switch main
git reset --hard <SHA_ANTERIOR_BOM>
```

Preferencialmente, crie primeiro uma branch de resgate para nao perder o estado anterior.

## Frequencia recomendada

- Diaria, se o fork acompanha upstream com frequencia.
- Antes de cada ciclo de integracao grande.
- Antes de mergear uma branch de adaptacao para `main`.
- Imediatamente antes de liberar uma versao interna.
