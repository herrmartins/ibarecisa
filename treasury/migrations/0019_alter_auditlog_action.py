import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treasury', '0018_migrate_old_schema_data'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                (
                    "CREATE TABLE IF NOT EXISTS \"treasury_periodsnapshot\" "
                    "(\"id\" char(32) NOT NULL PRIMARY KEY, "
                    "\"period_id\" char(32) NOT NULL, "
                    "\"period_month\" integer NOT NULL, "
                    "\"period_year\" integer NOT NULL, "
                    "\"created_at\" datetime NOT NULL, "
                    "\"created_by_id\" integer NULL, "
                    "\"created_by_name\" varchar(255) NOT NULL, "
                    "\"reason\" text NOT NULL, "
                    "\"snapshot_data\" json NOT NULL, "
                    "\"transactions_count\" integer NOT NULL DEFAULT 0, "
                    "\"closing_balance\" decimal(15,2) NULL, "
                    "\"was_closed\" bool NOT NULL DEFAULT 0)"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS \"audit_log\" "
                    "(\"id\" char(32) NOT NULL PRIMARY KEY, "
                    "\"timestamp\" datetime NOT NULL, "
                    "\"action\" varchar(50) NOT NULL, "
                    "\"entity_type\" varchar(50) NOT NULL, "
                    "\"entity_id\" integer NOT NULL, "
                    "\"old_values\" json NULL, "
                    "\"new_values\" json NULL, "
                    "\"description\" text NOT NULL, "
                    "\"snapshot_id\" char(32) NULL, "
                    "\"ip_address\" char(39) NULL, "
                    "\"user_agent\" text NOT NULL, "
                    "\"period_id\" integer NULL, "
                    "\"user_id\" integer NULL REFERENCES \"users_customuser\"(\"id\") ON DELETE SET NULL)"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS \"treasury_pe_period__4080e5_idx\" "
                    "ON \"treasury_periodsnapshot\" (\"period_id\", \"created_at\" DESC)"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS \"treasury_pe_created_8c2654_idx\" "
                    "ON \"treasury_periodsnapshot\" (\"created_by_id\")"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS \"treasury_pe_period__1fda6e_idx\" "
                    "ON \"treasury_periodsnapshot\" (\"period_month\", \"period_year\")"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS \"audit_log_timesta_8b04a8_idx\" "
                    "ON \"audit_log\" (\"timestamp\" DESC)"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS \"audit_log_action_b32d4d_idx\" "
                    "ON \"audit_log\" (\"action\")"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS \"audit_log_entity__c2633a_idx\" "
                    "ON \"audit_log\" (\"entity_type\", \"entity_id\")"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS \"audit_log_user_id_79f582_idx\" "
                    "ON \"audit_log\" (\"user_id\", \"timestamp\" DESC)"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS \"audit_log_period__e627c7_idx\" "
                    "ON \"audit_log\" (\"period_id\")"
                ),
            ],
            reverse_sql=[
                migrations.RunSQL.noop,
            ],
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(choices=[('period_opened', 'Período Aberto'), ('period_closed', 'Período Fechado'), ('period_reopened', 'Período Reaberto'), ('period_archived', 'Período Arquivado'), ('period_recalculated', 'Período Recalculado'), ('transaction_created', 'Transação Criada'), ('transaction_updated', 'Transação Atualizada'), ('transaction_deleted', 'Transação Deletada'), ('transaction_reversed', 'Transação Estornada'), ('snapshot_created', 'Snapshot Criado'), ('snapshot_restored', 'Snapshot Restaurado'), ('period_reset', 'Período Resetado'), ('period_restored', 'Período Restaurado'), ('report_generated', 'Relatório Gerado'), ('report_regenerated', 'Relatório Regenerado'), ('minute_created', 'Ata Criada'), ('minute_updated', 'Ata Atualizada'), ('minute_deleted', 'Ata Deletada'), ('minute_signed', 'Ata Assinada'), ('minute_pdf_generated', 'PDF de Ata Gerado'), ('excerpt_created', 'Excerto Criado'), ('excerpt_updated', 'Excerto Atualizado'), ('excerpt_deleted', 'Excerto Deletado'), ('template_created', 'Template Criado'), ('template_updated', 'Template Atualizado'), ('template_deleted', 'Template Deletado'), ('project_created', 'Projeto Criado'), ('project_updated', 'Projeto Atualizado'), ('project_deleted', 'Projeto Deletado'), ('file_uploaded', 'Arquivo Enviado'), ('file_deleted', 'Arquivo Deletado'), ('agenda_created', 'Agenda Criada'), ('agenda_updated', 'Agenda Atualizada'), ('agenda_deleted', 'Agenda Deletada')], db_index=True, help_text='Ação realizada', max_length=50),
        ),
    ]
