from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce

from treasury.models import (
    AccountingPeriod,
    TransactionModel,
    MonthlyReportModel,
)
from treasury.models.period_snapshot import PeriodSnapshot
from treasury.models.audit_log import AuditLog


FIXES = {
    '1': 'opening_balance',
    '2': 'closing_balance',
    '3': 'monthly_report',
    '4': 'orphan_transactions',
    '5': 'period_gaps',
    '6': 'all',
}

FIX_LABELS = {
    '1': 'Corrigir opening_balance',
    '2': 'Corrigir closing_balance (periodos fechados)',
    '3': 'Regenerar MonthlyReportModel',
    '4': 'Vincular transacoes orfas a periodos',
    '5': 'Criar periodos faltantes',
    '6': 'TUDO',
}


class Command(BaseCommand):
    help = 'Corrige inconsistencias na tesouraria'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fixes',
            type=str,
            help='Lista de correcoes separadas por virgula (ex: 1,2,3). Sem isso, abre menu interativo.',
        )
        parser.add_argument(
            '--month',
            type=str,
            help='Filtrar por mes (formato MM/AAAA, ex: 01/2024)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Mostra o que seria feito sem executar (PADRAO)',
        )
        parser.add_argument(
            '--no-dry-run',
            action='store_false',
            dest='dry_run',
            help='Executa as correcoes de verdade',
        )
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            default=False,
            help='Nao pedir confirmacao antes de cada correcao',
        )

    def handle(self, *args, **options):
        fixes_arg = options.get('fixes')
        month_arg = options.get('month')
        dry_run = options.get('dry_run', True)
        no_confirm = options.get('no_confirm', False)

        selected = self._resolve_fixes(fixes_arg)

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n  MODO DRY-RUN: Nenhuma alteracao sera feita.'
                '\n  Use --no-dry-run para executar de verdade.\n'
            ))

        period_qs = self._resolve_periods(month_arg)

        summary = {
            'dry_run': dry_run,
            'fixes_applied': [],
            'fixes_skipped': [],
            'errors': [],
        }

        for fix_key in selected:
            fix_name = FIXES[fix_key]
            self.stdout.write(f'\n{"=" * 60}')
            self.stdout.write(self.style.NOTICE(
                f'  [{fix_key}] {FIX_LABELS[fix_key]}'
                f'{" (DRY-RUN)" if dry_run else ""}'
            ))
            self.stdout.write(f'{"=" * 60}')

            if not no_confirm and not dry_run:
                answer = input(f'  Executar {FIX_LABELS[fix_key]}? (s/N): ').strip().lower()
                if answer != 's':
                    self.stdout.write(self.style.WARNING(f'  Pulando {FIX_LABELS[fix_key]}...'))
                    summary['fixes_skipped'].append(fix_name)
                    continue

            result = self._run_fix(fix_name, period_qs, dry_run)
            summary['fixes_applied'].append({
                'fix': fix_name,
                'result': result,
            })

            self._print_fix_result(result)

        self._print_summary(summary)

    def _resolve_fixes(self, fixes_arg):
        if fixes_arg:
            keys = [k.strip() for k in fixes_arg.split(',')]
            invalid = [k for k in keys if k not in FIXES]
            if invalid:
                self.stderr.write(self.style.ERROR(f'Correcao(oes) invalida(s): {", ".join(invalid)}'))
                self.stderr.write(f'Opcoes validas: {", ".join(FIXES.keys())}')
                raise SystemExit(1)
            if '6' in keys:
                return [k for k in FIXES.keys() if k != '6']
            return keys

        self.stdout.write(self.style.NOTICE('\nO que deseja corrigir?'))
        for k, label in FIX_LABELS.items():
            self.stdout.write(f'  [{k}] {label}')

        choice = input('\nOpcao: ').strip().upper()
        if choice == 'T' or choice == '6':
            return [k for k in FIXES.keys() if k != '6']
        keys = [k.strip() for k in choice.split(',')]
        invalid = [k for k in keys if k not in FIXES]
        if invalid:
            self.stderr.write(self.style.ERROR(f'Opcao invalida: {", ".join(invalid)}'))
            raise SystemExit(1)
        return keys

    def _resolve_periods(self, month_arg):
        qs = AccountingPeriod.objects.all().order_by('month')
        if month_arg:
            try:
                parts = month_arg.split('/')
                m, y = int(parts[0]), int(parts[1])
                target = date(y, m, 1)
                return AccountingPeriod.objects.filter(month=target).order_by('month')
            except (ValueError, IndexError):
                self.stderr.write(self.style.ERROR(f'Formato de mes invalido: {month_arg}. Use MM/AAAA'))
                raise SystemExit(1)
        return qs

    def _run_fix(self, fix_name, period_qs, dry_run):
        dispatch = {
            'opening_balance': self._fix_opening_balance,
            'closing_balance': self._fix_closing_balance,
            'monthly_report': self._fix_monthly_report,
            'orphan_transactions': self._fix_orphan_transactions,
            'period_gaps': self._fix_period_gaps,
        }
        return dispatch[fix_name](period_qs, dry_run)

    def _calculate_net(self, period):
        txs = TransactionModel.objects.filter(
            accounting_period=period,
            transaction_type='original',
        )
        positive_sum = txs.filter(is_positive=True).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total']
        neg_signed = txs.filter(is_positive=False, amount__lt=0).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total']
        neg_unsigned = txs.filter(is_positive=False, amount__gt=0).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total']
        return positive_sum + neg_signed - neg_unsigned

    def _create_snapshot_and_log(self, period, reason, dry_run):
        if dry_run:
            return None
        try:
            snapshot = PeriodSnapshot.create_from_period(
                period,
                created_by=None,
                reason=reason,
            )
            AuditLog.log(
                action='period_recalculated',
                entity_type='AccountingPeriod',
                entity_id=period.id,
                description=reason,
                snapshot_id=snapshot.id,
                period_id=period.id,
            )
            return snapshot
        except Exception:
            return None

    def _fix_opening_balance(self, period_qs, dry_run):
        result = {'fixed': 0, 'already_ok': 0, 'details': []}
        all_periods = list(AccountingPeriod.objects.all().order_by('month'))

        month_filter = None
        filtered = list(period_qs)
        if filtered:
            month_filter = {p.month for p in filtered}

        prev_closing = None

        for i, period in enumerate(all_periods):
            net = self._calculate_net(period)

            if month_filter and period.month not in month_filter:
                actual_opening = period.opening_balance
                if period.status in ('closed', 'archived') and period.closing_balance is not None:
                    prev_closing = period.closing_balance
                else:
                    prev_closing = actual_opening + net
                continue

            if period.is_first_month:
                result['details'].append({
                    'period': period.month.strftime('%m/%Y'),
                    'action': 'skip',
                    'message': f'is_first_month: mantido opening_balance={period.opening_balance}',
                })
                if period.status in ('closed', 'archived') and period.closing_balance is not None:
                    prev_closing = period.closing_balance
                else:
                    prev_closing = period.opening_balance + net
                continue

            if i == 0:
                result['details'].append({
                    'period': period.month.strftime('%m/%Y'),
                    'action': 'skip',
                    'message': f'Primeiro periodo: mantido opening_balance={period.opening_balance}',
                })
                if period.status in ('closed', 'archived') and period.closing_balance is not None:
                    prev_closing = period.closing_balance
                else:
                    prev_closing = period.opening_balance + net
                continue

            if prev_closing is None:
                prev_p = all_periods[i - 1]
                prev_net = self._calculate_net(prev_p)
                if prev_p.status in ('closed', 'archived') and prev_p.closing_balance is not None:
                    prev_closing = prev_p.closing_balance
                else:
                    prev_closing = prev_p.opening_balance + prev_net

            expected = prev_closing

            if period.opening_balance != expected:
                old = period.opening_balance
                if not dry_run:
                    self._create_snapshot_and_log(
                        period,
                        f'Correcao opening_balance: {old} -> {expected}',
                        dry_run,
                    )
                    period.opening_balance = expected
                    period.save(update_fields=['opening_balance'])

                result['fixed'] += 1
                result['details'].append({
                    'period': period.month.strftime('%m/%Y'),
                    'action': 'fixed',
                    'old': str(old),
                    'new': str(expected),
                    'message': f'{old} -> {expected}',
                })
            else:
                result['already_ok'] += 1
                result['details'].append({
                    'period': period.month.strftime('%m/%Y'),
                    'action': 'ok',
                    'message': f'OK: {period.opening_balance}',
                })

            if period.status in ('closed', 'archived') and period.closing_balance is not None:
                prev_closing = period.closing_balance
            else:
                prev_closing = period.opening_balance + net

        return result

    def _fix_closing_balance(self, period_qs, dry_run):
        result = {'fixed': 0, 'already_ok': 0, 'details': []}
        closed = period_qs.filter(
            status__in=['closed', 'archived'],
            closing_balance__isnull=False,
        )

        for period in closed:
            net = self._calculate_net(period)
            expected = period.opening_balance + net
            diff = period.closing_balance - expected

            if diff != Decimal('0'):
                old = period.closing_balance
                if not dry_run:
                    self._create_snapshot_and_log(
                        period,
                        f'Correcao closing_balance: {old} -> {expected}',
                        dry_run,
                    )
                    period.closing_balance = expected
                    period.save(update_fields=['closing_balance'])

                result['fixed'] += 1
                result['details'].append({
                    'period': period.month.strftime('%m/%Y'),
                    'action': 'fixed',
                    'old': str(old),
                    'new': str(expected),
                    'opening': str(period.opening_balance),
                    'net': str(net),
                    'message': f'{old} -> {expected}',
                })
            else:
                result['already_ok'] += 1
                result['details'].append({
                    'period': period.month.strftime('%m/%Y'),
                    'action': 'ok',
                    'message': f'OK: {period.closing_balance}',
                })

        if closed.count() == 0:
            result['details'].append({
                'action': 'info',
                'message': 'Nenhum periodo fechado encontrado.',
            })

        return result

    def _fix_monthly_report(self, period_qs, dry_run):
        result = {'fixed': 0, 'already_ok': 0, 'details': []}
        periods = list(AccountingPeriod.objects.all().order_by('month'))

        for period in periods:
            txs = TransactionModel.objects.filter(
                accounting_period=period,
                transaction_type='original',
            )

            positive = txs.filter(is_positive=True).aggregate(
                total=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total']
            neg_signed = txs.filter(is_positive=False, amount__lt=0).aggregate(
                total=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total']
            neg_unsigned = txs.filter(is_positive=False, amount__gt=0).aggregate(
                total=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total']
            negative = neg_signed - neg_unsigned
            net = positive + negative
            monthly_result = positive + negative
            total_balance = period.opening_balance + net

            prev_period = period.get_previous_period()
            previous_balance = Decimal('0.00')
            if prev_period:
                if prev_period.status in ('closed', 'archived') and prev_period.closing_balance is not None:
                    previous_balance = prev_period.closing_balance
                else:
                    previous_balance = prev_period.opening_balance + self._calculate_net(prev_period)

            report = MonthlyReportModel.objects.filter(month=period.month).first()

            needs_fix = False
            if not report:
                needs_fix = True
            else:
                if (report.previous_month_balance != previous_balance or
                        report.total_positive_transactions != positive or
                        report.total_negative_transactions != negative or
                        report.monthly_result != monthly_result or
                        report.total_balance != total_balance):
                    needs_fix = True

            if needs_fix:
                if not dry_run:
                    MonthlyReportModel.objects.filter(month=period.month).delete()
                    MonthlyReportModel.objects.create(
                        month=period.month,
                        previous_month_balance=previous_balance,
                        total_positive_transactions=positive,
                        total_negative_transactions=negative,
                        in_cash=Decimal('0.00'),
                        in_current_account=Decimal('0.00'),
                        in_savings_account=Decimal('0.00'),
                        monthly_result=monthly_result,
                        total_balance=total_balance,
                    )

                result['fixed'] += 1
                action = 'created' if not report else 'updated'
                result['details'].append({
                    'period': period.month.strftime('%m/%Y'),
                    'action': action,
                    'data': {
                        'previous_month_balance': str(previous_balance),
                        'total_positive': str(positive),
                        'total_negative': str(negative),
                        'monthly_result': str(monthly_result),
                        'total_balance': str(total_balance),
                    },
                    'message': (
                        f'{"Criado" if action == "created" else "Atualizado"}: '
                        f'prev={previous_balance}, +{positive}, -{negative}, '
                        f'result={monthly_result}, total={total_balance}'
                    ),
                })
            else:
                result['already_ok'] += 1
                result['details'].append({
                    'period': period.month.strftime('%m/%Y'),
                    'action': 'ok',
                    'message': 'OK',
                })

        return result

    def _fix_orphan_transactions(self, period_qs, dry_run):
        result = {'fixed': 0, 'already_ok': 0, 'details': []}
        orphans = TransactionModel.objects.filter(accounting_period__isnull=True)

        if not orphans.exists():
            result['details'].append({
                'action': 'ok',
                'message': 'Nenhuma transacao orfa encontrada.',
            })
            return result

        for tx in orphans:
            period_month = tx.date.replace(day=1)
            period, created = AccountingPeriod.objects.get_or_create(
                month=period_month,
                defaults={'status': 'open', 'opening_balance': Decimal('0.00')},
            )

            if created and not dry_run:
                prev_period = period.get_previous_period()
                if prev_period and prev_period.closing_balance:
                    period.opening_balance = prev_period.closing_balance
                    period.save(update_fields=['opening_balance'])

            if not dry_run:
                tx.accounting_period = period
                tx.save(update_fields=['accounting_period'])

            result['fixed'] += 1
            result['details'].append({
                'transaction_id': tx.id,
                'date': str(tx.date),
                'description': tx.description,
                'action': 'fixed',
                'period': period_month.strftime('%m/%Y'),
                'period_created': created,
                'message': (
                    f'TX #{tx.id} ({tx.date} - {tx.description}) '
                    f'-> periodo {period_month.strftime("%m/%Y")}'
                    f'{" (periodo criado)" if created else ""}'
                ),
            })

        return result

    def _fix_period_gaps(self, period_qs, dry_run):
        result = {'fixed': 0, 'already_ok': 0, 'details': []}
        all_periods = AccountingPeriod.objects.all().order_by('month')

        if not all_periods.exists():
            result['details'].append({
                'action': 'info',
                'message': 'Nenhum periodo existente.',
            })
            return result

        first = all_periods.first().month
        current = timezone.now().date().replace(day=1)
        cursor = first
        expected_months = []
        while cursor <= current:
            expected_months.append(cursor)
            if cursor.month == 12:
                cursor = cursor.replace(year=cursor.year + 1, month=1)
            else:
                cursor = cursor.replace(month=cursor.month + 1)

        existing = {p.month for p in all_periods}
        gaps = [m for m in expected_months if m not in existing]

        if not gaps:
            result['details'].append({
                'action': 'ok',
                'message': 'Nenhum gap encontrado.',
            })
            return result

        for gap_month in sorted(gaps):
            prev_month = gap_month
            if prev_month.month == 1:
                prev_month_date = gap_month.replace(year=gap_month.year - 1, month=12, day=1)
            else:
                prev_month_date = gap_month.replace(month=gap_month.month - 1)

            opening = Decimal('0.00')
            prev_period = AccountingPeriod.objects.filter(month=prev_month_date).first()
            if prev_period:
                opening = prev_period.opening_balance + self._calculate_net(prev_period)

            if not dry_run:
                AccountingPeriod.objects.create(
                    month=gap_month,
                    opening_balance=opening,
                    status='open',
                )

            result['fixed'] += 1
            result['details'].append({
                'month': gap_month.strftime('%m/%Y'),
                'action': 'created',
                'opening_balance': str(opening),
                'message': f'Criado periodo {gap_month.strftime("%m/%Y")} com opening={opening}',
            })

        return result

    def _print_fix_result(self, result):
        fixed = result.get('fixed', 0)
        ok = result.get('already_ok', 0)

        for detail in result.get('details', []):
            action = detail.get('action', 'info')
            msg = detail.get('message', '')

            if action in ('fixed', 'created', 'updated'):
                self.stdout.write(self.style.SUCCESS(f'  + {msg}'))
            elif action == 'ok':
                self.stdout.write(self.style.SUCCESS(f'  OK {msg}'))
            elif action == 'skip':
                self.stdout.write(f'  i {msg}')
            else:
                self.stdout.write(f'  i {msg}')

        self.stdout.write(f'\n  Corrigidos: {fixed} | Ja OK: {ok}')

    def _print_summary(self, summary):
        self.stdout.write(f'\n{"=" * 60}')
        self.stdout.write(self.style.NOTICE('  RESUMO FINAL'))
        self.stdout.write(f'{"=" * 60}')

        if summary['dry_run']:
            self.stdout.write(self.style.WARNING(
                '  MODO DRY-RUN: Nada foi alterado.'
            ))
            self.stdout.write('  Use --no-dry-run para aplicar as correcoes.')

        for entry in summary['fixes_applied']:
            fix = entry['fix']
            res = entry['result']
            self.stdout.write(f'  {fix}: {res.get("fixed", 0)} corrigido(s), {res.get("already_ok", 0)} OK')

        if summary['fixes_skipped']:
            self.stdout.write(self.style.WARNING(
                f'  Pulados: {", ".join(summary["fixes_skipped"])}'))

        self.stdout.write('')
