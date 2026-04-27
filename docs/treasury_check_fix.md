# Tesouraria: Verificacao e Correcao de Inconsistencias

Dois management commands para diagnosticar e corrigir problemas na tesouraria.

## Comandos

### `check_treasury` — Verificar inconsistencias

```bash
python manage.py check_treasury
```

Abre um menu interativo para escolher o que verificar.

**Opcoes via CLI:**

```bash
# Verificar itens especificos
python manage.py check_treasury --checks 1,2,3

# Filtrar por mes
python manage.py check_treasury --checks 1 --month 01/2024

# Gerar JSON
python manage.py check_treasury --checks 1,2,3,4,5,6,8,9,10 --output json
python manage.py check_treasury --output json --json-file resultado.json
```

**Verificacoes disponiveis:**

| # | Verificacao | O que faz |
|---|------------|-----------|
| 1 | Cadeia de opening_balance | Verifica se cada periodo herda o saldo correto do anterior |
| 2 | Closing_balance | Verifica se `opening + net == closing` nos periodos fechados |
| 3 | MonthlyReportModel | Compara os campos do relatorio com as transacoes reais |
| 4 | Periodos faltantes | Detecta meses sem periodo entre o primeiro e o atual |
| 5 | Transacoes orfas | Encontra transacoes sem `accounting_period` |
| 6 | Estornos | Verifica estornos sem original, duplicados, ou estorno de estorno |
| 7 | FrozenReport hash | Verifica integridade SHA256 dos PDFs congelados |
| 8 | is_first_month | Verifica se ha apenas 1 primeiro periodo e se e o mais antigo |
| 9 | Running balance | Simula a cadeia completa do primeiro ao ultimo periodo |
| 10 | Consistencia de sinal | Detecta mistura de padroes de sinal no campo `amount` |
| T | TUDO | Executa todas as verificacoes |

---

### `fix_treasury` — Corrigir inconsistencias

```bash
# Sempre comeca em modo dry-run (nao altera nada)
python manage.py fix_treasury
```

**Opcoes via CLI:**

```bash
# Modo interativo
python manage.py fix_treasury

# Ver o que seria corrigido (dry-run, padrao)
python manage.py fix_treasury --fixes 1,2 --month 03/2024

# Executar de verdade
python manage.py fix_treasury --fixes 1,2 --no-dry-run

# Sem confirmacao (para scripts/cron)
python manage.py fix_treasury --fixes 1,2,3 --no-dry-run --no-confirm

# Corrigir tudo
python manage.py fix_treasury --fixes 6 --no-dry-run
```

**Correcoes disponiveis:**

| # | Correcao | O que faz |
|---|----------|-----------|
| 1 | opening_balance | Recalcula a cadeia de saldos de abertura |
| 2 | closing_balance | Corrige `closing_balance` dos periodos fechados |
| 3 | MonthlyReportModel | Deleta e recria os relatorios a partir das transacoes reais |
| 4 | Transacoes orfas | Vincula transacoes sem periodo ao periodo correto |
| 5 | Periodos faltantes | Cria periodos para meses sem periodo |
| 6 | TUDO | Executa todas as correcoes |

**Seguranca:**

- **dry-run e o padrao**: nunca altera nada sem `--no-dry-run`
- **Snapshot automatico**: antes de cada correcao, cria um `PeriodSnapshot`
- **AuditLog**: registra toda correcao no log de auditoria
- **Confirmacao**: pede confirmacao antes de cada correcao (desativa com `--no-confirm`)

---

## Fluxo recomendado

```bash
# 1. Verificar tudo
python manage.py check_treasury --checks T

# 2. Ver o que seria corrigido (dry-run)
python manage.py fix_treasury --fixes 6

# 3. Se concordar, executar
python manage.py fix_treasury --fixes 6 --no-dry-run

# 4. Verificar novamente
python manage.py check_treasury --checks T
```

## Corrigir apenas um mes

```bash
# Verificar
python manage.py check_treasury --checks 1,2,3 --month 03/2024

# Corrigir
python manage.py fix_treasury --fixes 1,2,3 --month 03/2024 --no-dry-run
```

## Nota tecnica: duplo padrao de sinal

O banco contem dois padroes de armazenamento para transacoes negativas:

| Padrao | is_positive | amount | Epoca |
|--------|------------|--------|-------|
| Antigo | False | **negativo** (ex: -973.52) | Dados migrados / inicio do sistema |
| Novo | False | **positivo** (ex: 450.00) | Entradas recentes |

Os scripts lidam com ambos automaticamente usando:
```python
neg_signed = Sum(amount) onde is_positive=False E amount < 0   # ja com sinal
neg_unsigned = Sum(amount) onde is_positive=False E amount > 0  # precisa negativar
net = positive + neg_signed - neg_unsigned
```

A verificacao [10] (Consistencia de sinal) alerta quando ha mistura de padroes.

## Agendamento (cron)

```bash
# Verificacao diaria com JSON
0 2 * * * cd /path/to/project && python manage.py check_treasury --checks 1,2,3,4,5,6,8,9,10 --output json --json-file /var/log/treasury_check.json
```

---

## Diagnostico e Restauracao (Superuser)

### `treasury_diagnosis` — Relatorio completo do estado

```bash
# Terminal interativo
python manage.py treasury_diagnosis

# JSON (para scripts)
python manage.py treasury_diagnosis --output json
python manage.py treasury_diagnosis --output json --json-file diag.json
```

**O que diagnostica:**
- Status de todos os periodos (aberto/fechado/arquivado)
- Cadeia de saldos (opening_balance herda do closing_balance anterior?)
- Transacoes orfas (sem accounting_period)
- Gaps entre periodos
- Mistura de padroes de sinal
- Transacoes vinculadas ao periodo errado
- Snapshots disponiveis para restore
- Auditoria recente

**Pagina web:** `/treasury/admin/diagnostico/` (apenas superuser)

---

### `snapshot_period` — Criar ponto de restauracao

```bash
python manage.py snapshot_period --month 01/2024 --reason "Antes de editar"
```

Cria um `PeriodSnapshot` com todas as transacoes e saldos. Permite restaurar depois.

---

### `restore_period` — Restaurar a partir de snapshot

```bash
# Ver o que seria restaurado (dry-run)
python manage.py restore_period --snapshot-id UUID --dry-run

# Executar restauracao
python manage.py restore_period --snapshot-id UUID --no-confirm

# Com usuario para auditoria
python manage.py restore_period --snapshot-id UUID --user-id 1
```

**O que faz:**
1. Cria auto-snapshot do estado atual (para reverter o restore)
2. Deleta transacoes, estornos, relatorios e frozen reports do periodo
3. Recria transacoes a partir do snapshot
4. Registra tudo no AuditLog

---

## Fluxo: Editar periodo fechado

```bash
# 1. Diagnosticar
python manage.py treasury_diagnosis

# 2. Criar snapshot antes de reabrir
python manage.py snapshot_period --month 01/2024 --reason "Antes de reabrir para edicao"

# 3. Reabrir (via dashboard ou API)
# Dashboard: /treasury/admin/diagnostico/ -> botao "Reabrir"
# API: POST /treasury/api/diagnosis/reopen/ { period_id: X }

# 4. Editar/transacoes livremente

# 5. Se algo deu errado, restaurar:
python manage.py restore_period --snapshot-id UUID
```

## Bugs corrigidos

| Bug | Arquivo | Correcao |
|-----|---------|----------|
| `TransactionUpdateSerializer` checava `is_closed` em vez de `not is_open` | `serializers/__init__.py` | Período `archived` agora também bloqueia edição |
| `TransactionViewSet.perform_destroy` sem verificação de período | `api/views.py` | Adicionado bloqueio para períodos fechados/arquivados |
| `TransactionListSerializer` sem `can_be_reversed` | `serializers/__init__.py` | Botão "Estornar" agora aparece na lista de transações |
