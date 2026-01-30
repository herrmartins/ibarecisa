from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date
from calendar import monthrange

from treasury.models import TransactionModel, AccountingPeriod
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Migra transações existentes para o modelo de períodos contábeis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria feito sem executar',
        )
        parser.add_argument(
            '--close-periods',
            action='store_true',
            help='Fecha os períodos automaticamente após migrar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        close_periods = options['close_periods']

        self.stdout.write(self.style.WARNING('=== Migração para Períodos Contábeis ==='))

        # 1. Encontrar todas as transações sem período
        transactions_without_period = TransactionModel.objects.filter(
            accounting_period__isnull=True
        ).order_by('date')

        count = transactions_without_period.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ Todas as transações já estão vinculadas a períodos.'))
            return

        self.stdout.write(f'\nEncontradas {count} transações sem período vinculado.')

        # 2. Agrupar transações por mês
        from collections import defaultdict
        transactions_by_month = defaultdict(list)
        for tx in transactions_without_period:
            month_key = (tx.date.year, tx.date.month)
            transactions_by_month[month_key].append(tx)

        self.stdout.write(f'\nMeses a processar: {len(transactions_by_month)}')

        # 3. Para cada mês, criar ou atualizar o período
        months_sorted = sorted(transactions_by_month.keys())
        running_balance = Decimal('0.00')

        for i, (year, month) in enumerate(months_sorted):
            month_date = date(year, month, 1)
            transactions = transactions_by_month[(year, month)]

            # Calcular totais do mês
            positive_total = sum(tx.amount for tx in transactions if tx.is_positive)
            negative_total = sum(tx.amount for tx in transactions if not tx.is_positive)
            net_change = positive_total - negative_total

            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'  {month_date.strftime("%B/%Y").capitalize()}')
            self.stdout.write(f'{"="*60}')
            self.stdout.write(f'  Transações: {len(transactions)}')
            self.stdout.write(f'  Receitas:   R$ {positive_total:,.2f}')
            self.stdout.write(f'  Despesas:   R$ {negative_total:,.2f}')
            self.stdout.write(f'  Saldo Mês:  R$ {net_change:,.2f}')
            self.stdout.write(f'  Saldo Acum: R$ {running_balance + net_change:,.2f}')

            if dry_run:
                self.stdout.write('  [DRY-RUN] Criaria período e vincularia transações')
                running_balance += net_change
                continue

            # Verificar se período já existe
            period, created = AccountingPeriod.objects.get_or_create(
                month=month_date,
                defaults={
                    'opening_balance': running_balance,
                    'status': 'open',
                }
            )

            if created:
                self.stdout.write(f'  ✓ Período criado (opening_balance: R$ {running_balance:,.2f})')
            else:
                self.stdout.write(f'  ℹ Período já existe, atualizando...')

            # Vincular transações ao período
            updated_count = transactions_without_period.filter(
                date__year=year,
                date__month=month
            ).update(accounting_period=period)

            self.stdout.write(f'  ✓ {updated_count} transações vinculadas')

            # Fechar período se solicitado (e não for o mês atual)
            should_close = close_periods and month_date < date.today().replace(day=1)
            if should_close:
                period.closing_balance = running_balance + net_change
                period.status = 'closed'
                period.closed_at = timezone.now()
                period.save()
                self.stdout.write(f'  ✓ Período FECHADO (closing_balance: R$ {period.closing_balance:,.2f})')

            running_balance += net_change

        # 4. Resumo final
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('RESUMO:')
        self.stdout.write(f'  Total de transações processadas: {count}')
        self.stdout.write(f'  Total de meses: {len(months_sorted)}')
        self.stdout.write(f'  Saldo final acumulado: R$ {running_balance:,.2f}')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✓ Migração concluída com sucesso!'))

            # Verificar transações órfãs
            remaining = TransactionModel.objects.filter(accounting_period__isnull=True).count()
            if remaining > 0:
                self.stdout.write(self.style.WARNING(f'\n⚠ Ainda há {remaining} transações sem período (possivelmente com datas futuras ou inválidas)'))
            else:
                self.stdout.write(self.style.SUCCESS('✓ Todas as transações foram vinculadas a períodos!'))
        else:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN] Nenhuma alteração foi feita. Use --dry-run=False para executar.'))

