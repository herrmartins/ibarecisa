from django.core.management.base import BaseCommand
from treasury.models import AccountingPeriod
from decimal import Decimal


class Command(BaseCommand):
    help = 'Corrige o opening_balance para todos os AccountingPeriods'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria corrigido sem fazer alterações',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'MODO DRY-RUN: Nenhuma alteração será feita\n'))

        periods = AccountingPeriod.objects.all().order_by('month')
        total_periods = periods.count()
        ok_count = 0
        fixed_count = 0

        self.stdout.write(f'Total de períodos: {total_periods}\n')

        for period in periods:
            prev_period = period.get_previous_period()

            if prev_period:
                # Calcular o opening_balance esperado
                if prev_period.closing_balance is not None:
                    expected_opening = prev_period.closing_balance
                else:
                    # Período anterior está aberto - usar saldo atual
                    expected_opening = prev_period.get_current_balance()

                if period.opening_balance != expected_opening:
                    self.stdout.write(
                        self.style.WARNING(
                            f'CORRIGIR {period.month_name}/{period.year}: '
                            f'de {period.opening_balance} para {expected_opening}'
                        )
                    )
                    fixed_count += 1

                    if not dry_run:
                        period.opening_balance = expected_opening
                        period.save(update_fields=['opening_balance'])
                else:
                    self.stdout.write(
                        f'OK {period.month_name}/{period.year}: {period.opening_balance}'
                    )
                    ok_count += 1
            else:
                # Primeiro período - deve ser 0 ou definido manualmente
                self.stdout.write(
                    f'PRIMEIRO {period.month_name}/{period.year}: {period.opening_balance}'
                )
                ok_count += 1

        # Resumo
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Total de períodos: {total_periods}')
        self.stdout.write(f'Períodos OK: {ok_count}')
        self.stdout.write(f'Períodos a corrigir: {fixed_count}')

        if fixed_count > 0:
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'\n {fixed_count} períodos seriam corrigidos'))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'\n {fixed_count} períodos corrigidos!'))
        else:
            self.stdout.write(self.style.SUCCESS(
                '\n✓ Todos os períodos já estão corretos!'))
