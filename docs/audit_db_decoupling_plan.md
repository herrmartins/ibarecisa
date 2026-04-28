# Plano: Desacoplar Banco de Auditoria

## Objetivo

Tornar o `audit.sqlite3` **opcional e removível**. O sistema principal (default DB) nunca deve quebrar se o banco de auditoria estiver ausente, movido ou corrompido. Isso permite arquivar o banco de auditoria anualmente (ex: `audit_2024.sqlite3`) sem interromper o funcionamento.

---

## Estado Atual

### Banco de auditoria (`audit.sqlite3`) contém:

| Model | Impacto se ausente | Protegido? |
|-------|-------------------|------------|
| `AuditLog` | Nenhum - `AuditLog.log()` já tem try/except | SIM |
| `PeriodSnapshot` | **QUEBRA** o fechamento de período e reabertura | NAO |
| `FrozenReport` | Ja tem try/except no `_create_frozen_reports()` | SIM |

### Pontos criticos (sem protecao):

1. **`AccountingPeriod.close()`** - `treasury/models/accounting_period.py:234`
   - Chama `PeriodSnapshot.create_from_period()` diretamente
   - Se audit DB nao existe → excecao → periodo nao fecha

2. **`PeriodService.create_snapshot()`** - `treasury/services/period_service.py:486`
   - Chama `PeriodSnapshot.create_from_period()` diretamente

3. **`PeriodService.reopen_period_with_snapshot()`** - `treasury/services/period_service.py:507`
   - Chama `self.create_snapshot()` que chama o PeriodSnapshot diretamente

4. **`fix_treasury` command** - `treasury/management/commands/fix_treasury.py:187`
   - Chama `PeriodSnapshot.create_from_period()` diretamente

5. **`treasury_diagnosis` command** - `treasury/management/commands/treasury_diagnosis.py:76,254`
   - Chama `PeriodSnapshot.objects.count()` e `.all()` diretamente

6. **`diagnosis_views.py` API** - `treasury/api/diagnosis_views.py:56,166,219,251,260,341`
   - Multiplos acessos diretos a PeriodSnapshot

---

## Implementacao

### Passo 1: Criar `treasury/services/audit_service.py`

Helper que envolve todas as operacoes do audit DB em try/except:

```python
import logging
from django.db import OperationalError, DatabaseError

logger = logging.getLogger(__name__)


def safe_create_snapshot(period, user=None, reason=''):
    """Cria snapshot se o banco audit estiver disponivel. Nao quebra se nao estiver."""
    try:
        from treasury.models import PeriodSnapshot
        return PeriodSnapshot.create_from_period(period, created_by=user, reason=reason)
    except (OperationalError, DatabaseError) as e:
        logger.warning(f"Audit DB indisponivel, snapshot nao criado: {e}")
        return None
    except Exception as e:
        logger.warning(f"Erro ao criar snapshot: {e}")
        return None


def safe_audit_log(**kwargs):
    """Cria log de auditoria se o banco estiver disponivel."""
    try:
        from treasury.models import AuditLog
        return AuditLog.log(**kwargs)
    except (OperationalError, DatabaseError) as e:
        logger.warning(f"Audit DB indisponivel, log nao criado: {e}")
        return None
    except Exception:
        return None


def safe_get_snapshots(period_id=None, limit=20):
    """Busca snapshots. Retorna lista vazia se indisponivel."""
    try:
        from treasury.models import PeriodSnapshot
        qs = PeriodSnapshot.objects.all().order_by('-created_at')
        if period_id:
            qs = qs.filter(period_id=period_id)
        return list(qs[:limit])
    except Exception:
        return []


def safe_get_audit_logs(entity_types=None, limit=30):
    """Busca logs de auditoria. Retorna lista vazia se indisponivel."""
    try:
        from treasury.models import AuditLog
        qs = AuditLog.objects.all().order_by('-timestamp')
        if entity_types:
            qs = qs.filter(entity_type__in=entity_types)
        return list(qs[:limit])
    except Exception:
        return []


def safe_get_snapshot_count():
    """Retorna count de snapshots. Retorna 0 se indisponivel."""
    try:
        from treasury.models import PeriodSnapshot
        return PeriodSnapshot.objects.count()
    except Exception:
        return 0


def safe_get_frozen_report_exists(period):
    """Verifica se existe frozen report. Retorna False se indisponivel."""
    try:
        from treasury.models import FrozenReport
        return FrozenReport.objects.filter(period=period).exists()
    except Exception:
        return False


def is_audit_db_available():
    """Verifica se o banco de auditoria esta acessivel."""
    try:
        from treasury.models import PeriodSnapshot
        PeriodSnapshot.objects.count()
        return True
    except Exception:
        return False
```

### Passo 2: Alterar `AccountingPeriod.close()` 

**Arquivo:** `treasury/models/accounting_period.py`

Linha 232-238, substituir:
```python
# ANTES (quebra se audit DB nao existe):
from treasury.models.period_snapshot import PeriodSnapshot
PeriodSnapshot.create_from_period(
    self,
    created_by=user,
    reason=f'Fechamento do periodo {self.month_name}/{self.year}'
)
```

Por:
```python
# DEPOIS (nao quebra):
from treasury.services.audit_service import safe_create_snapshot
safe_create_snapshot(
    self,
    user=user,
    reason=f'Fechamento do periodo {self.month_name}/{self.year}'
)
```

### Passo 3: Alterar `PeriodService`

**Arquivo:** `treasury/services/period_service.py`

#### `create_snapshot()` (linha ~486):
```python
# ANTES:
return PeriodSnapshot.create_from_period(period, user, reason)

# DEPOIS:
from treasury.services.audit_service import safe_create_snapshot
return safe_create_snapshot(period, user, reason)
```

#### `reopen_period_with_snapshot()` (linha ~507):
```python
# ANTES:
snapshot = self.create_snapshot(period, user, reason)

# DEPOIS:
snapshot = self.create_snapshot(period, user, reason)  # Ja usa safe_create_snapshot
```

Nota: como `create_snapshot()` ja vai usar `safe_create_snapshot()`, `reopen_period_with_snapshot()` fica protegido automaticamente. Mas os downstreams que leem `snapshot.id` precisam checar se `snapshot is not None`.

### Passo 4: Alterar `fix_treasury.py`

**Arquivo:** `treasury/management/commands/fix_treasury.py` (linha ~187)

```python
# ANTES:
snapshot = PeriodSnapshot.create_from_period(period, user, reason)

# DEPOIS:
from treasury.services.audit_service import safe_create_snapshot
snapshot = safe_create_snapshot(period, user, reason)
```

Adicionar protecao nos lugares que leem `snapshot.id`:
```python
if snapshot:
    # ... codigo que usa snapshot.id
```

### Passo 5: Alterar `treasury_diagnosis.py`

**Arquivo:** `treasury/management/commands/treasury_diagnosis.py`

```python
# No topo, adicionar:
from treasury.services.audit_service import (
    safe_get_snapshot_count,
    safe_get_snapshots,
    safe_get_audit_logs,
    safe_get_frozen_report_exists,
    is_audit_db_available,
)

# Substituir PeriodSnapshot.objects.count() → safe_get_snapshot_count()
# Substituir PeriodSnapshot.objects.all() → safe_get_snapshots()
# Substituir FrozenReport.objects.filter(period=period).exists() → safe_get_frozen_report_exists(period)
# Substituir AuditLog.objects.filter() → safe_get_audit_logs()

# Adicionar no report:
report['audit_db_available'] = is_audit_db_available()
```

No terminal output, mostrar:
```
  Audit DB: DISPONIVEL  (ou "INDISPONIVEL" em vermelho)
```

### Passo 6: Alterar `diagnosis_views.py` (API)

**Arquivo:** `treasury/api/diagnosis_views.py`

```python
from treasury.services.audit_service import (
    safe_get_snapshots,
    safe_get_audit_logs,
    safe_get_snapshot_count,
    safe_get_frozen_report_exists,
    is_audit_db_available,
    safe_create_snapshot,
)

# Substituir todos os acessos diretos a PeriodSnapshot/FrozenReport/AuditLog
# Adicionar no response:
report['audit_db_available'] = is_audit_db_available()
```

Nas views de acao (snapshot/restore/reopen), proteger os snapshots:
```python
# DiagnosisReopenView:
snapshot = safe_create_snapshot(period, user=request.user, reason=...)
# snapshot pode ser None - nao usar snapshot.id sem checar

# DiagnosisRestoreView:
try:
    snapshot = PeriodSnapshot.objects.get(id=snapshot_id)
except PeriodSnapshot.DoesNotExist:
    return Response({'error': 'Snapshot nao encontrado'}, status=404)
except Exception:
    return Response({'error': 'Banco de auditoria indisponivel'}, status=503)
```

### Passo 7: Template de diagnostico

**Arquivo:** `treasury/templates/treasury/admin/diagnosis.html`

Adicionar badge no summary:
```html
<div class="bg-white rounded-lg shadow p-4">
    <p class="text-xs text-gray-500 uppercase">Audit DB</p>
    <p x-show="report.audit_db_available" class="text-sm font-bold text-green-600">Disponivel</p>
    <p x-show="!report.audit_db_available" class="text-sm font-bold text-red-600">Indisponivel</p>
</div>
```

---

## Testes a adicionar

**Arquivo:** `treasury/tests/test_diagnosis.py`

```python
class AuditDBDecouplingTests(DiagnosisTestBase):
    
    def test_close_period_works_without_audit_db(self):
        """Fechar periodo nao quebra mesmo se PeriodSnapshot falhar"""
        # Mock safe_create_snapshot para retornar None (simula DB indisponivel)
        # Verificar que o periodo fecha corretamente
        # Verificar que closing_balance fica correto
        
    def test_diagnosis_with_audit_db_unavailable(self):
        """Diagnostico funciona mesmo sem audit DB"""
        # Mock is_audit_db_available retornar False
        # Verificar que o report retorna com audit_db_available=False
        
    def test_safe_create_snapshot_returns_none_on_error(self):
        """Helper retorna None em vez de excecao"""
        from treasury.services.audit_service import safe_create_snapshot
        # Forcar OperationalError
        # Verificar retorna None
        
    def test_safe_get_snapshots_returns_empty_on_error(self):
        """Helper retorna lista vazia em vez de excecao"""
        from treasury.services.audit_service import safe_get_snapshots
        # Forcar erro
        # Verificar retorna []
        
    def test_snapshot_period_command_with_audit_unavailable(self):
        """Comando snapshot_period nao quebra se audit DB indisponivel"""
        # Mock PeriodSnapshot.create_from_period para lancar OperationalError
        # Verificar que o comando nao quebra
```

---

## Fluxo de arquivamento anual

Depois de implementado, o processo de arquivamento sera:

```bash
# 1. Verificar que tudo esta ok
python manage.py treasury_diagnosis

# 2. Parar a aplicacao

# 3. Mover o banco antigo
mv audit.sqlite3 audit_2024.sqlite3

# 4. Criar novo banco vazio
python manage.py migrate --database=audit

# 5. Reiniciar a aplicacao

# 6. Verificar que tudo funciona (audit_db_available=True no diagnostico)
python manage.py treasury_diagnosis
```

O sistema continua funcionando normalmente entre os passos 3 e 4, sem o banco de auditoria.

---

## Arquivos a criar/alterar

| Acao | Arquivo |
|------|---------|
| CRIAR | `treasury/services/audit_service.py` |
| ALTERAR | `treasury/models/accounting_period.py` (linha 232-238) |
| ALTERAR | `treasury/services/period_service.py` (linhas 486, 507) |
| ALTERAR | `treasury/management/commands/fix_treasury.py` (linha 187) |
| ALTERAR | `treasury/management/commands/treasury_diagnosis.py` (linhas 76, 133, 254) |
| ALTERAR | `treasury/api/diagnosis_views.py` (multiplos pontos) |
| ALTERAR | `treasury/templates/treasury/admin/diagnosis.html` (badge audit DB) |
| ALTERAR | `treasury/tests/test_diagnosis.py` (novos testes) |

---

## Ordem de execucao

1. Criar `audit_service.py`
2. Alterar `accounting_period.py` (close)
3. Alterar `period_service.py` (create_snapshot, reopen)
4. Alterar `fix_treasury.py`
5. Alterar `treasury_diagnosis.py`
6. Alterar `diagnosis_views.py`
7. Alterar template `diagnosis.html`
8. Adicionar testes
9. Rodar testes: `python manage.py test treasury.tests.test_diagnosis -v 2`
10. Atualizar este documento com resultado
