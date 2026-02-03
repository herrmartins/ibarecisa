from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class AuditLog(models.Model):
    """
    Registro de auditoria de alterações no sistema.

    Armazena no banco separado (audit.sqlite3) todo histórico de
    alterações para fins de compliance e auditoria externa.

    IMPORTANTE: Não usa ForeignKey para models de outros bancos
    (cross-db foreign keys não funcionam), apenas referências por ID.
    """

    ACTION_CHOICES = [
        # Períodos
        ('period_opened', 'Período Aberto'),
        ('period_closed', 'Período Fechado'),
        ('period_reopened', 'Período Reaberto'),
        ('period_archived', 'Período Arquivado'),
        ('period_recalculated', 'Período Recalculado'),

        # Transações
        ('transaction_created', 'Transação Criada'),
        ('transaction_updated', 'Transação Atualizada'),
        ('transaction_deleted', 'Transação Deletada'),
        ('transaction_reversed', 'Transação Estornada'),

        # Snapshots
        ('snapshot_created', 'Snapshot Criado'),
        ('snapshot_restored', 'Snapshot Restaurado'),

        # Relatórios
        ('report_generated', 'Relatório Gerado'),
        ('report_regenerated', 'Relatório Regenerado'),

        # Secretaria - Atas
        ('minute_created', 'Ata Criada'),
        ('minute_updated', 'Ata Atualizada'),
        ('minute_deleted', 'Ata Deletada'),
        ('minute_signed', 'Ata Assinada'),
        ('minute_pdf_generated', 'PDF de Ata Gerado'),

        # Secretaria - Excertos
        ('excerpt_created', 'Excerto Criado'),
        ('excerpt_updated', 'Excerto Atualizado'),
        ('excerpt_deleted', 'Excerto Deletado'),

        # Secretaria - Templates
        ('template_created', 'Template Criado'),
        ('template_updated', 'Template Atualizado'),
        ('template_deleted', 'Template Deletado'),

        # Secretaria - Projetos
        ('project_created', 'Projeto Criado'),
        ('project_updated', 'Projeto Atualizado'),
        ('project_deleted', 'Projeto Deletado'),

        # Secretaria - Arquivos
        ('file_uploaded', 'Arquivo Enviado'),
        ('file_deleted', 'Arquivo Deletado'),

        # Secretaria - Agenda
        ('agenda_created', 'Agenda Criada'),
        ('agenda_updated', 'Agenda Atualizada'),
        ('agenda_deleted', 'Agenda Deletada'),
    ]

    ENTITY_TYPE_CHOICES = [
        # Tesouraria
        ('AccountingPeriod', 'Período Contábil'),
        ('TransactionModel', 'Transação'),
        ('PeriodSnapshot', 'Snapshot de Período'),
        ('MonthlyReportModel', 'Relatório Mensal'),
        ('CategoryModel', 'Categoria'),

        # Secretaria
        ('MeetingMinuteModel', 'Ata'),
        ('MinuteExcerptsModel', 'Excerto'),
        ('MinuteTemplateModel', 'Template'),
        ('MinuteProjectModel', 'Projeto'),
        ('MinuteFileModel', 'Arquivo'),
        ('MeetingAgendaModel', 'Agenda'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Quem fez a alteração (sem FK para evitar cross-db)
    user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID do usuário que fez a alteração"
    )
    user_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nome do usuário que fez a alteração"
    )

    # O que foi alterado
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Ação realizada"
    )
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        db_index=True,
        help_text="Tipo de entidade afetada"
    )
    entity_id = models.IntegerField(
        db_index=True,
        help_text="ID da entidade afetada (sem FK por ser cross-db)"
    )

    # Dados da alteração
    old_values = models.JSONField(
        null=True,
        blank=True,
        help_text="Valores antes da alteração"
    )
    new_values = models.JSONField(
        null=True,
        blank=True,
        help_text="Valores após a alteração"
    )

    # Contexto adicional
    description = models.TextField(
        blank=True,
        help_text="Descrição opcional da alteração"
    )

    # Referência ao snapshot (se aplicável) - apenas o UUID como texto
    snapshot_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="UUID do snapshot relacionado (se houver)"
    )

    # Metadados para rastreabilidade
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP de onde veio a requisição"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent do navegador"
    )

    # Campos para facilitar consultas
    period_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID do período contábil relacionado (para filtros rápidos)"
    )
    minute_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID da ata relacionada (para filtros rápidos)"
    )

    class Meta:
        app_label = 'treasury'
        db_table = 'audit_log'
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['action']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['user_id', '-timestamp']),
            models.Index(fields=['period_id']),
            models.Index(fields=['minute_id']),
        ]

    def __str__(self):
        user_str = self.user_name if self.user_name else 'Sistema'
        return f"{self.timestamp.strftime('%d/%m/%Y %H:%M')} - {user_str}: {self.get_action_display()}"

    @classmethod
    def log(cls, action, entity_type, entity_id, user=None, old_values=None,
            new_values=None, description='', snapshot_id=None, period_id=None,
            minute_id=None, request=None):
        """
        Método auxiliar para criar log de auditoria.

        Args:
            action: Ação realizada (choices do model)
            entity_type: Tipo da entidade afetada
            entity_id: ID da entidade
            user: Usuário que fez a alteração
            old_values: Valores antes (dict)
            new_values: Valores depois (dict)
            description: Descrição opcional
            snapshot_id: UUID do snapshot relacionado
            period_id: ID do período contábil
            minute_id: ID da ata relacionada
            request: Objeto HttpRequest (para extrair IP e user agent)

        Returns:
            Instância de AuditLog criada
        """
        ip_address = None
        user_agent = ''

        if request:
            # Extrair IP de forma segura
            meta = getattr(request, 'META', None) or {}
            x_forwarded_for = meta.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = meta.get('REMOTE_ADDR')

            # Extrair user agent de forma segura
            user_agent = meta.get('HTTP_USER_AGENT', '')[:500]

        # Extrair info do usuário (sem FK)
        user_id_value = None
        user_name_value = ''
        if user:
            user_id_value = user.id
            user_name_value = user.get_full_name() or user.username

        return cls.objects.create(
            user_id=user_id_value,
            user_name=user_name_value,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            description=description,
            snapshot_id=snapshot_id,
            period_id=period_id,
            minute_id=minute_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
