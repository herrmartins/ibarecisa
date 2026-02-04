"""
Signals para auditoria automática da secretaria.

Registra automaticamente criações, alterações e exclusões de:
- MeetingMinuteModel (Atas)
- MinuteExcerptsModel (Excertos)
- MinuteTemplateModel (Templates)
- MinuteProjectModel (Projetos)
- MinuteFileModel (Arquivos)
- MeetingAgendaModel (Agendas)
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from treasury.models import AuditLog
from secretarial.models import (
    MeetingMinuteModel,
    MinuteExcerptsModel,
    MinuteTemplateModel,
    MinuteProjectModel,
    MinuteFileModel,
    MeetingAgendaModel,
)

User = get_user_model()


def get_user_from_instance(instance):
    """
    Tenta obter o usuário que está fazendo a alteração.
    Busca em campos comuns como 'created_by', 'updated_by', 'user', etc.
    """
    for field in ['created_by', 'updated_by', 'user', 'author']:
        if hasattr(instance, field):
            value = getattr(instance, field)
            if value and isinstance(value, User):
                return value
    return None


@receiver(pre_save, sender=MeetingMinuteModel)
def track_minute_old_values(sender, instance, **kwargs):
    """Armazena valores antigos antes de atualizar uma ata."""
    if instance.pk:
        try:
            old_instance = MeetingMinuteModel.objects.get(pk=instance.pk)
            instance._audit_old_values = {
                'president': old_instance.president_id,
                'secretary': old_instance.secretary_id,
                'meeting_date': old_instance.meeting_date.isoformat() if old_instance.meeting_date else None,
                'number_of_attendees': old_instance.number_of_attendees,
                'body': old_instance.body[:200] + '...' if old_instance.body and len(old_instance.body) > 200 else old_instance.body,
            }
        except MeetingMinuteModel.DoesNotExist:
            instance._audit_old_values = None


@receiver(post_save, sender=MeetingMinuteModel)
def log_minute_changes(sender, instance, created, **kwargs):
    """Registra criação ou atualização de ata."""
    user = get_user_from_instance(instance)

    if created:
        AuditLog.log(
            action='minute_created',
            entity_type='MeetingMinuteModel',
            entity_id=instance.pk,
            user=user,
            new_values={
                'president': instance.president_id,
                'secretary': instance.secretary_id,
                'meeting_date': instance.meeting_date.isoformat() if instance.meeting_date else None,
                'number_of_attendees': instance.number_of_attendees,
            },
            minute_id=instance.pk,
            description=f"Ata criada para {instance.meeting_date}",
        )
    else:
        old_values = getattr(instance, '_audit_old_values', None)
        if old_values:
            AuditLog.log(
                action='minute_updated',
                entity_type='MeetingMinuteModel',
                entity_id=instance.pk,
                user=user,
                old_values=old_values,
                new_values={
                    'president': instance.president_id,
                    'secretary': instance.secretary_id,
                    'meeting_date': instance.meeting_date.isoformat() if instance.meeting_date else None,
                },
                minute_id=instance.pk,
                description=f"Ata atualizada: {instance}",
            )


@receiver(post_delete, sender=MeetingMinuteModel)
def log_minute_deletion(sender, instance, **kwargs):
    """Registra exclusão de ata."""
    user = get_user_from_instance(instance)
    AuditLog.log(
        action='minute_deleted',
        entity_type='MeetingMinuteModel',
        entity_id=instance.pk,
        user=user,
        old_values={
            'meeting_date': instance.meeting_date.isoformat() if instance.meeting_date else None,
        },
        minute_id=instance.pk,
        description=f"Ata deletada: {instance}",
    )


@receiver(post_save, sender=MinuteExcerptsModel)
def log_excerpt_changes(sender, instance, created, **kwargs):
    """Registra criação ou atualização de excerto."""
    user = get_user_from_instance(instance)
    action = 'excerpt_created' if created else 'excerpt_updated'

    AuditLog.log(
        action=action,
        entity_type='MinuteExcerptsModel',
        entity_id=instance.pk,
        user=user,
        new_values={
            'title': instance.title[:100] if hasattr(instance, 'title') else None,
        },
        minute_id=instance.minute_id if hasattr(instance, 'minute_id') else None,
        description=f"Excerto {action.replace('excerpt_', '')}: {instance}",
    )


@receiver(post_delete, sender=MinuteExcerptsModel)
def log_excerpt_deletion(sender, instance, **kwargs):
    """Registra exclusão de excerto."""
    user = get_user_from_instance(instance)
    AuditLog.log(
        action='excerpt_deleted',
        entity_type='MinuteExcerptsModel',
        entity_id=instance.pk,
        user=user,
        minute_id=instance.minute_id if hasattr(instance, 'minute_id') else None,
        description=f"Excerto deletado: {instance}",
    )


@receiver(post_save, sender=MinuteTemplateModel)
def log_template_changes(sender, instance, created, **kwargs):
    """Registra criação ou atualização de template."""
    user = get_user_from_instance(instance)
    action = 'template_created' if created else 'template_updated'

    AuditLog.log(
        action=action,
        entity_type='MinuteTemplateModel',
        entity_id=instance.pk,
        user=user,
        new_values={
            'name': instance.name[:100] if hasattr(instance, 'name') else None,
        },
        description=f"Template {action.replace('template_', '')}: {instance}",
    )


@receiver(post_delete, sender=MinuteTemplateModel)
def log_template_deletion(sender, instance, **kwargs):
    """Registra exclusão de template."""
    user = get_user_from_instance(instance)
    AuditLog.log(
        action='template_deleted',
        entity_type='MinuteTemplateModel',
        entity_id=instance.pk,
        user=user,
        description=f"Template deletado: {instance}",
    )


@receiver(post_save, sender=MinuteProjectModel)
def log_project_changes(sender, instance, created, **kwargs):
    """Registra criação ou atualização de projeto."""
    user = get_user_from_instance(instance)
    action = 'project_created' if created else 'project_updated'

    AuditLog.log(
        action=action,
        entity_type='MinuteProjectModel',
        entity_id=instance.pk,
        user=user,
        new_values={
            'title': instance.title[:100] if hasattr(instance, 'title') else None,
        },
        minute_id=instance.minute_id if hasattr(instance, 'minute_id') else None,
        description=f"Projeto {action.replace('project_', '')}: {instance}",
    )


@receiver(post_delete, sender=MinuteProjectModel)
def log_project_deletion(sender, instance, **kwargs):
    """Registra exclusão de projeto."""
    user = get_user_from_instance(instance)
    AuditLog.log(
        action='project_deleted',
        entity_type='MinuteProjectModel',
        entity_id=instance.pk,
        user=user,
        minute_id=instance.minute_id if hasattr(instance, 'minute_id') else None,
        description=f"Projeto deletado: {instance}",
    )


@receiver(post_save, sender=MinuteFileModel)
def log_file_upload(sender, instance, created, **kwargs):
    """Registra upload de arquivo."""
    if created:
        user = get_user_from_instance(instance)
        AuditLog.log(
            action='file_uploaded',
            entity_type='MinuteFileModel',
            entity_id=instance.pk,
            user=user,
            new_values={
                'filename': instance.file.name if hasattr(instance, 'file') else None,
            },
            minute_id=instance.minute_id if hasattr(instance, 'minute_id') else None,
            description=f"Arquivo enviado: {instance}",
        )


@receiver(post_delete, sender=MinuteFileModel)
def log_file_deletion(sender, instance, **kwargs):
    """Registra exclusão de arquivo."""
    user = get_user_from_instance(instance)
    AuditLog.log(
        action='file_deleted',
        entity_type='MinuteFileModel',
        entity_id=instance.pk,
        user=user,
        minute_id=instance.minute_id if hasattr(instance, 'minute_id') else None,
        description=f"Arquivo deletado: {instance}",
    )


@receiver(post_save, sender=MeetingAgendaModel)
def log_agenda_changes(sender, instance, created, **kwargs):
    """Registra criação ou atualização de agenda."""
    user = get_user_from_instance(instance)
    action = 'agenda_created' if created else 'agenda_updated'

    AuditLog.log(
        action=action,
        entity_type='MeetingAgendaModel',
        entity_id=instance.pk,
        user=user,
        new_values={
            'title': instance.title[:100] if hasattr(instance, 'title') else None,
        },
        description=f"Agenda {action.replace('agenda_', '')}: {instance}",
    )


@receiver(post_delete, sender=MeetingAgendaModel)
def log_agenda_deletion(sender, instance, **kwargs):
    """Registra exclusão de agenda."""
    user = get_user_from_instance(instance)
    AuditLog.log(
        action='agenda_deleted',
        entity_type='MeetingAgendaModel',
        entity_id=instance.pk,
        user=user,
        description=f"Agenda deletada: {instance}",
    )
