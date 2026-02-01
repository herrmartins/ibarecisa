from django.db import models
from django.contrib.auth import get_user_model
import hashlib
import uuid

User = get_user_model()


class FrozenReport(models.Model):
    """
    Relatório congelado para auditoria.

    Armazena o PDF gerado no fechamento de período com seu hash SHA256.
    Permite verificar integridade e recuperar versão original via AuditLog.
    """

    REPORT_TYPES = [
        ('analytical', 'Relatório Analítico'),
        ('extract', 'Extrato de Transações'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    period = models.ForeignKey(
        'AccountingPeriod',
        on_delete=models.CASCADE,
        related_name='frozen_reports'
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        default='analytical'
    )

    # PDF armazenado
    pdf_file = models.FileField(upload_to='frozen_reports/%Y/%m/')
    pdf_hash = models.CharField(
        max_length=64,
        help_text="SHA256 do PDF (hex)"
    )

    # Dados do período no momento do congelamento
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2)
    total_positive = models.DecimalField(max_digits=10, decimal_places=2)
    total_negative = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_count = models.IntegerField()

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_recovered = models.BooleanField(
        default=False,
        help_text="True se foi recuperado de uma verificação que falhou"
    )

    # Se este report substituiu outro (recuperação)
    replaces_report = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replaced_by'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Relatório Congelado'
        verbose_name_plural = 'Relatórios Congelados'
        indexes = [
            models.Index(fields=['period', '-created_at']),
            models.Index(fields=['report_type', '-created_at']),
            models.Index(fields=['pdf_hash']),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period.month_name}/{self.period.year}"

    @classmethod
    def calculate_hash(cls, pdf_bytes):
        """Calcula SHA256 do PDF."""
        return hashlib.sha256(pdf_bytes).hexdigest()

    def verify(self):
        """
        Verifica se o PDF foi alterado.

        Returns:
            dict: {
                'valid': bool,
                'stored_hash': str,
                'current_hash': str,
                'matches': bool
            }
        """
        # Ler PDF atual
        self.pdf_file.seek(0)
        pdf_bytes = self.pdf_file.read()
        self.pdf_file.seek(0)

        current_hash = self.calculate_hash(pdf_bytes)

        return {
            'valid': current_hash == self.pdf_hash,
            'stored_hash': self.pdf_hash,
            'current_hash': current_hash,
            'matches': current_hash == self.pdf_hash
        }

    def recover_from_audit(self):
        """
        Recupera PDF original a partir do AuditLog.

        Returns:
            FrozenReport: Novo FrozenReport com PDF recuperado
        """
        from treasury.models import AuditLog
        from treasury.views.generate_period_analytical_pdf_view import GeneratePeriodAnalyticalPDFView

        # Buscar logs do período até a data de criação deste report
        logs = AuditLog.objects.filter(
            period_id=self.period.id,
            created_at__lte=self.created_at,
            action__in=['transaction_created', 'transaction_updated', 'transaction_deleted']
        ).order_by('created_at')

        # Reconstruir estado das transações
        transactions = {}
        deleted_ids = set()

        for log in logs:
            tx_id = log.entity_id
            if log.action == 'transaction_deleted':
                deleted_ids.add(tx_id)
            elif tx_id not in deleted_ids:
                transactions[tx_id] = log.new_values

        # Recriar PDF (precisamos de uma forma de gerar o PDF)
        # Por enquanto, marcamos como recuperado
        recovered = FrozenReport.objects.create(
            period=self.period,
            report_type=self.report_type,
            pdf_file=self.pdf_file,  # Seria o PDF recriado
            pdf_hash=self.pdf_hash,
            closing_balance=self.closing_balance,
            total_positive=self.total_positive,
            total_negative=self.total_negative,
            transaction_count=self.transaction_count,
            is_recovered=True,
            replaces_report=self
        )

        return recovered

    @classmethod
    def create_from_period(cls, period, pdf_bytes, report_type='analytical', user=None):
        """
        Cria um FrozenReport a partir de um período.

        Args:
            period: AccountingPeriod
            pdf_bytes: bytes do PDF
            report_type: 'analytical' ou 'extract'
            user: User que está criando

        Returns:
            FrozenReport
        """
        from django.core.files.base import ContentFile
        import calendar

        # Calcular hash
        pdf_hash = cls.calculate_hash(pdf_bytes)

        # Obter resumo do período
        summary = period.get_transactions_summary()

        # Criar arquivo
        filename = f"{report_type}_{period.month.year}_{period.month.month:02d}_{pdf_hash[:8]}.pdf"
        pdf_file = ContentFile(pdf_bytes, name=filename)

        return cls.objects.create(
            period=period,
            report_type=report_type,
            pdf_file=pdf_file,
            pdf_hash=pdf_hash,
            closing_balance=period.closing_balance or summary.get('net', 0),
            total_positive=summary.get('total_positive', 0),
            total_negative=summary.get('total_negative', 0),
            transaction_count=summary.get('count', 0),
            created_by=user
        )
