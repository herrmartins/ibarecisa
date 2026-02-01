from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class PeriodSnapshot(models.Model):
    """
    Snapshot do estado de um período contábil antes de alterações significativas.

    Usado para manter histórico de como o período estava antes de:
    - Reabertura para estornos
    - Recálculo em cascata
    - Alterações manuais

    Permite auditoria e comparação de estados.

    NOTA: Usa period_id e created_by_id em vez de ForeignKeys para permitir
    salvar no banco de auditoria separado (sem relações cross-database).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # ID do período (sem ForeignKey para evitar cross-db)
    period_id = models.UUIDField(
        help_text="ID do AccountingPeriod (referência sem FK)"
    )
    # Metadados do período armazenados diretamente para consulta fácil
    period_month = models.IntegerField(help_text="Mês do período (1-12)")
    period_year = models.IntegerField(help_text="Ano do período")

    created_at = models.DateTimeField(auto_now_add=True)
    # ID do usuário (sem ForeignKey para evitar cross-db)
    created_by_id = models.IntegerField(null=True, help_text="ID do usuário que criou o snapshot")
    created_by_name = models.CharField(max_length=255, blank=True, help_text="Nome do usuário que criou")

    reason = models.TextField(
        help_text="Motivo da criação do snapshot (ex: 'Reabertura para estorno da transação #123')"
    )

    # Estado snapshot em JSON
    snapshot_data = models.JSONField(
        help_text="Dados completos do período no momento do snapshot"
    )

    # Metadados para facilitar consulta
    transactions_count = models.IntegerField(default=0)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    was_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Snapshot de Período'
        verbose_name_plural = 'Snapshots de Períodos'
        indexes = [
            models.Index(fields=['period_id', '-created_at']),
            models.Index(fields=['created_by_id']),
            models.Index(fields=['period_month', 'period_year']),
        ]

    def __str__(self):
        return f"Snapshot de {self.period_month:02d}/{self.period_year} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    def get_closing_balance(self):
        """Retorna o saldo final armazenado no snapshot."""
        return self.snapshot_data.get('summary', {}).get('closing_balance') or self.closing_balance

    @classmethod
    def create_from_period(cls, period, created_by=None, reason=""):
        """
        Cria um snapshot a partir de um AccountingPeriod.

        Args:
            period: Instância de AccountingPeriod
            created_by: Instância do User (opcional)
            reason: Motivo do snapshot
        """
        from treasury.services.period_service import PeriodService

        # Obtém os dados do snapshot via service
        snapshot_data = PeriodService.get_period_snapshot_data(period)

        return cls.objects.create(
            period_id=period.id,
            period_month=period.month.month,
            period_year=period.month.year,
            created_by_id=created_by.id if created_by else None,
            created_by_name=created_by.get_full_name() or created_by.username if created_by else '',
            reason=reason,
            snapshot_data=snapshot_data,
            transactions_count=snapshot_data.get('summary', {}).get('transactions_count', 0),
            closing_balance=snapshot_data.get('summary', {}).get('closing_balance'),
            was_closed=(period.status == 'closed')
        )
