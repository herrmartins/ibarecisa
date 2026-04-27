from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone

from treasury.models import (
    AccountingPeriod,
    TransactionModel,
    ReversalTransaction,
    PeriodSnapshot,
    AuditLog,
    MonthlyReportModel,
    FrozenReport,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Restaura um período a partir de um snapshot (reverte alterações)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--snapshot-id', type=str, required=True,
            help='UUID do snapshot para restaurar',
        )
        parser.add_argument(
            '--user-id', type=int, required=False,
            help='ID do superuser que está restaurando',
        )
        parser.add_argument(
            '--dry-run', action='store_true', default=False,
            help='Simula a restauração sem alterar nada',
        )
        parser.add_argument(
            '--no-confirm', action='store_true', default=False,
            help='Pula confirmação interativa',
        )

    def handle(self, *args, **options):
        snapshot_id = options['snapshot_id']
        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)
        no_confirm = options.get('no_confirm', False)

        try:
            snapshot = PeriodSnapshot.objects.get(id=snapshot_id)
        except PeriodSnapshot.DoesNotExist:
            raise CommandError(f'Snapshot {snapshot_id} não encontrado')

        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f'Usuário {user_id} não encontrado')

        try:
            period = AccountingPeriod.objects.get(id=snapshot.period_id)
        except AccountingPeriod.DoesNotExist:
            raise CommandError(
                f'Período {snapshot.period_id} não encontrado. '
                f'O snapshot é de {snapshot.period_month:02d}/{snapshot.period_year}.'
            )

        self.stdout.write(f'\n  Snapshot: {snapshot}')
        self.stdout.write(f'  Período:  {period.month_name}/{period.year} (status: {period.status})')
        self.stdout.write(f'  Criado em: {snapshot.created_at.strftime("%d/%m/%Y %H:%M")}')
        self.stdout.write(f'  Motivo: {snapshot.reason}')
        self.stdout.write(f'  Transações no snapshot: {snapshot.transactions_count}')

        current_tx = TransactionModel.objects.filter(
            accounting_period=period,
            transaction_type='original',
        ).count()
        self.stdout.write(f'  Transações atuais: {current_tx}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n  [DRY RUN] Nenhuma alteração será feita.'))
            self._show_diff(snapshot, period)
            return

        if not no_confirm:
            confirm = input('\n  Confirmar restauração? (sim/não): ')
            if confirm.lower() not in ('sim', 's', 'yes', 'y'):
                self.stdout.write('  Cancelado.')
                return

        self._restore(snapshot, period, user)

    def _show_diff(self, snapshot, period):
        data = snapshot.snapshot_data
        snap_txs = data.get('transactions', [])
        snap_summary = data.get('summary', {})

        self.stdout.write(f'\n  Saldo no snapshot:')
        self.stdout.write(f'    Opening: {snap_summary.get("opening_balance", "?")}')
        self.stdout.write(f'    Closing: {snap_summary.get("closing_balance", "?")}')
        self.stdout.write(f'    Net: {snap_summary.get("net", "?")}')

        current_txs = TransactionModel.objects.filter(
            accounting_period=period,
        ).order_by('date', 'created_at')

        self.stdout.write(f'\n  Transações atuais no período ({current_txs.count()}):')
        for tx in current_txs[:20]:
            sign = '+' if tx.is_positive else '-'
            self.stdout.write(f'    #{tx.id} {tx.date} {sign}R${tx.amount} {tx.description}')

        self.stdout.write(f'\n  Transações no snapshot ({len(snap_txs)}):')
        for tx in snap_txs[:20]:
            sign = '+' if tx.get('is_positive') else '-'
            self.stdout.write(f'    #{tx.get("id")} {tx.get("date")} {sign}R${tx.get("amount")} {tx.get("description")}')

    def _restore(self, snapshot, period, user):
        data = snapshot.snapshot_data
        snap_txs = data.get('transactions', [])
        snap_summary = data.get('summary', {})

        pre_restore_snapshot = PeriodSnapshot.create_from_period(
            period,
            created_by=user,
            reason=f'Auto-snapshot antes de restore do snapshot {snapshot.id}',
        )

        ReversalTransaction.objects.filter(
            original_transaction__accounting_period=period,
        ).delete()
        ReversalTransaction.objects.filter(
            reversal_transaction__accounting_period=period,
        ).delete()

        TransactionModel.objects.filter(
            accounting_period=period,
            transaction_type='reversal',
        ).delete()

        TransactionModel.objects.filter(
            accounting_period=period,
            transaction_type='original',
        ).delete()

        MonthlyReportModel.objects.filter(month=period.month).delete()
        FrozenReport.objects.filter(period=period).delete()

        restored_count = 0
        for tx_data in snap_txs:
            try:
                category = None
                if tx_data.get('category'):
                    from treasury.models import CategoryModel
                    category = CategoryModel.objects.filter(
                        name=tx_data['category']
                    ).first()

                TransactionModel.objects.create(
                    user=user or User.objects.first(),
                    created_by=user,
                    accounting_period=period,
                    description=tx_data.get('description', ''),
                    amount=Decimal(str(tx_data.get('amount', 0))),
                    is_positive=tx_data.get('is_positive', True),
                    date=date.fromisoformat(tx_data['date']),
                    category=category,
                    transaction_type='original',
                )
                restored_count += 1
            except Exception as e:
                self.stderr.write(f'  Erro ao restaurar transação: {e}')

        if snap_summary.get('opening_balance') is not None:
            period.opening_balance = Decimal(str(snap_summary['opening_balance']))
            period.save(update_fields=['opening_balance'])

        AuditLog.log(
            action='period_restored',
            entity_type='AccountingPeriod',
            entity_id=period.id,
            user=user,
            old_values={
                'pre_restore_snapshot_id': str(pre_restore_snapshot.id),
                'from_snapshot_id': str(snapshot.id),
            },
            new_values={
                'restored_transactions': restored_count,
                'period_status': period.status,
            },
            description=(
                f'Restore do período {period.month_name}/{period.year} '
                f'a partir do snapshot {snapshot.id}. '
                f'{restored_count} transações restauradas.'
            ),
            period_id=period.id,
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n  Restauração concluída!\n'
            f'    {restored_count} transações restauradas\n'
            f'    Pre-restore snapshot: {pre_restore_snapshot.id}\n'
            f'    Para reverter esta restauração: '
            f'python manage.py restore_period --snapshot-id {pre_restore_snapshot.id}\n'
        ))
