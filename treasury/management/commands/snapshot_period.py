from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from treasury.models import AccountingPeriod, PeriodSnapshot, AuditLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria um snapshot (ponto de restauração) de um período contábil aberto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month', type=str, required=True,
            help='Mês no formato MM/YYYY (ex: 01/2024)',
        )
        parser.add_argument(
            '--user-id', type=int, required=False,
            help='ID do usuário que está criando o snapshot',
        )
        parser.add_argument(
            '--reason', type=str, default='',
            help='Motivo do snapshot (ex: "Antes de editar transações em massa")',
        )

    def handle(self, *args, **options):
        month_str = options['month']
        user_id = options.get('user_id')
        reason = options.get('reason', '')

        try:
            month, year = month_str.split('/')
            month = int(month)
            year = int(year)
        except (ValueError, AttributeError):
            raise CommandError('Formato inválido. Use MM/YYYY (ex: 01/2024)')

        from datetime import date
        try:
            period_date = date(year, month, 1)
        except ValueError:
            raise CommandError(f'Data inválida: {month_str}')

        try:
            period = AccountingPeriod.objects.get(month=period_date)
        except AccountingPeriod.DoesNotExist:
            raise CommandError(f'Período {month_str} não encontrado')

        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f'Usuário com ID {user_id} não encontrado')

        if not reason:
            reason = f'Snapshot manual do período {period.month_name}/{period.year}'

        snapshot = PeriodSnapshot.create_from_period(
            period,
            created_by=user,
            reason=reason,
        )

        AuditLog.log(
            action='snapshot_created',
            entity_type='AccountingPeriod',
            entity_id=period.id,
            user=user,
            new_values={
                'snapshot_id': str(snapshot.id),
                'period_month': f'{month:02d}/{year}',
                'period_status': period.status,
                'transactions_count': snapshot.transactions_count,
                'closing_balance': float(snapshot.closing_balance) if snapshot.closing_balance else None,
            },
            description=f'Snapshot manual criado: {reason}',
            period_id=period.id,
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Snapshot criado com sucesso!\n'
            f'  Período: {period.month_name}/{period.year} (status: {period.status})\n'
            f'  Snapshot ID: {snapshot.id}\n'
            f'  Transações: {snapshot.transactions_count}\n'
            f'  Motivo: {reason}\n'
            f'\n'
            f'  Para restaurar: python manage.py restore_period --snapshot-id {snapshot.id}\n'
        ))
