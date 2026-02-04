"""
Model for storing AI-generated financial insights.
"""
from django.db import models
from django.core.exceptions import ValidationError


class AIInsight(models.Model):
    """
    Armazena insights de IA gerados para um período específico.

    O cache é invalidado automaticamente se o número de transações
    mudar, garantindo que insights sempre reflitam os dados atuais.
    """
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    content = models.TextField(help_text='Conteúdo markdown dos insights gerados')
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Controle de invalidação de cache
    transactions_count = models.PositiveIntegerField(
        help_text='Número de transações usadas para gerar o insight. '
                  'Se mudar, o cache é invalidado.'
    )

    # Metadata para rastreamento
    model_used = models.CharField(
        max_length=50,
        help_text='Modelo de IA usado (ex: ollama/ministral-3:8b, mistral-small-latest)'
    )
    debug_mode = models.BooleanField(
        default=True,
        help_text='Se estava em DEBUG mode (Ollama) ou produção (Mistral API)'
    )

    class Meta:
        db_table = 'treasury_ai_insights'
        verbose_name = 'Insight de IA'
        verbose_name_plural = 'Insights de IA'
        # Um insight por período único
        constraints = [
            models.UniqueConstraint(
                fields=['start_date', 'end_date'],
                name='unique_ai_insight_period'
            )
        ]
        ordering = ['-generated_at']

    def __str__(self):
        return f"Insight IA {self.start_date} a {self.end_date}"

    def clean(self):
        """Valida que start_date <= end_date."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({'start_date': 'Data inicial deve ser anterior ou igual à data final.'})

    def is_still_valid(self, current_count: int) -> bool:
        """
        Verifica se o insight ainda é válido baseado no count de transações.

        Args:
            current_count: Número atual de transações no período

        Returns:
            True se o cache ainda é válido, False caso contrário
        """
        return self.transactions_count == current_count

    @property
    def is_stale(self) -> bool:
        """
        Retorna True se o insight tem mais de 30 dias.

        Útil para decidir se deve regerar mesmo que válido.
        """
        from datetime import timedelta
        from django.utils import timezone

        return timezone.now() - self.generated_at > timedelta(days=30)
