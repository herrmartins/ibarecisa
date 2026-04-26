import json
from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Q, Count, Case, When, F
from django.db.models.functions import Coalesce
from django.db import models as db_models

from treasury.models import (
    AccountingPeriod,
    TransactionModel,
    MonthlyReportModel,
    FrozenReport,
)


CHECKS = {
    '1': 'opening_balance',
    '2': 'closing_balance',
    '3': 'monthly_report',
    '4': 'period_gaps',
    '5': 'orphan_transactions',
    '6': 'reversal_integrity',
    '7': 'frozen_report_hash',
    '8': 'first_month',
    '9': 'running_balance',
    '10': 'amount_sign',
}

CHECK_LABELS = {
    '1': 'Cadeia de opening_balance',
    '2': 'Closing_balance de periodos fechados',
    '3': 'MonthlyReportModel vs transacoes reais',
    '4': 'Periodos faltantes (gaps)',
    '5': 'Transacoes orfas',
    '6': 'Integridade de estornos',
    '7': 'Hash de FrozenReports',
    '8': 'is_first_month',
    '9': 'Saldo corrente global (running balance)',
    '10': 'Consistencia de sinal do amount',
}


class Command(BaseCommand):
    help = 'Verifica inconsistencias na tesouraria'

    def add_arguments(self, parser):
        parser.add_argument(
            '--checks',
            type=str,
            help='Lista de checks separados por virgula (ex: 1,2,3). Sem isso, abre menu interativo.',
        )
        parser.add_argument(
            '--month',
            type=str,
            help='Filtrar por mes (formato MM/AAAA, ex: 01/2024)',
        )
        parser.add_argument(
            '--output',
            type=str,
            choices=['terminal', 'json'],
            default='terminal',
            help='Formato de saida (padrao: terminal)',
        )
        parser.add_argument(
            '--json-file',
            type=str,
            default=None,
            help='Caminho do arquivo JSON de saida (padrao: treasury_check_TIMESTAMP.json)',
        )

    def handle(self, *args, **options):
        checks_arg = options.get('checks')
        month_arg = options.get('month')
        output = options.get('output', 'terminal')
        json_file = options.get('json_file')

        selected = self._resolve_checks(checks_arg)
        period_qs = self._resolve_periods(month_arg)

        results = {}
        errors_count = 0
        warnings_count = 0

        for check_key in selected:
            check_name = CHECKS[check_key]
            self.stdout.write(f'\n{"=" * 60}')
            self.stdout.write(self.style.NOTICE(f'  [{check_key}] {CHECK_LABELS[check_key]}'))
            self.stdout.write(f'{"=" * 60}')

            result = self._run_check(check_name, period_qs)
            results[check_name] = result

            if output == 'terminal':
                self._print_result(check_name, result)

            errors_count += result.get('errors', 0)
            warnings_count += result.get('warnings', 0)

        self.stdout.write(f'\n{"=" * 60}')
        self.stdout.write(self.style.NOTICE('  RESUMO'))
        self.stdout.write(f'{"=" * 60}')

        if errors_count == 0 and warnings_count == 0:
            self.stdout.write(self.style.SUCCESS('  Tudo OK! Nenhuma inconsistencia encontrada.'))
        else:
            if errors_count > 0:
                self.stdout.write(self.style.ERROR(f'  Erros: {errors_count}'))
            if warnings_count > 0:
                self.stdout.write(self.style.WARNING(f'  Avisos: {warnings_count}'))

        if output == 'json' or json_file:
            filename = json_file or f'treasury_check_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str, ensure_ascii=False)
            self.stdout.write(self.style.SUCCESS(f'\n  JSON salvo em: {filename}'))

    def _resolve_checks(self, checks_arg):
        if checks_arg:
            keys = [k.strip() for k in checks_arg.split(',')]
            invalid = [k for k in keys if k not in CHECKS]
            if invalid:
                self.stderr.write(self.style.ERROR(f'Check(s) invalido(s): {", ".join(invalid)}'))
                self.stderr.write(f'Opcoes validas: {", ".join(CHECKS.keys())}')
                raise SystemExit(1)
            return keys

        self.stdout.write(self.style.NOTICE('\nO que deseja verificar?'))
        for k, label in CHECK_LABELS.items():
            self.stdout.write(f'  [{k}] {label}')
        self.stdout.write(f'  [T] TUDO')

        choice = input('\nOpcao: ').strip().upper()
        if choice == 'T':
            return list(CHECKS.keys())
        keys = [k.strip() for k in choice.split(',')]
        invalid = [k for k in keys if k not in CHECKS]
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

    def _run_check(self, check_name, period_qs):
        dispatch = {
            'opening_balance': self._check_opening_balance,
            'closing_balance': self._check_closing_balance,
            'monthly_report': self._check_monthly_report,
            'period_gaps': self._check_period_gaps,
            'orphan_transactions': self._check_orphan_transactions,
            'reversal_integrity': self._check_reversal_integrity,
            'frozen_report_hash': self._check_frozen_report_hash,
            'first_month': self._check_first_month,
            'running_balance': self._check_running_balance,
            'amount_sign': self._check_amount_sign,
        }
        return dispatch[check_name](period_qs)

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

    def _check_opening_balance(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}
        periods = list(period_qs)

        for i, period in enumerate(periods):
            if i == 0:
                result['details'].append({
                    'period': str(period),
                    'month': period.month.strftime('%m/%Y'),
                    'status': 'info',
                    'message': f'Primeiro periodo: opening={period.opening_balance}',
                })
                continue

            prev = periods[i - 1]
            if prev.closing_balance is not None:
                expected = prev.closing_balance
            else:
                expected = prev.opening_balance + self._calculate_net(prev)

            if period.opening_balance != expected:
                result['errors'] += 1
                diff = period.opening_balance - expected
                result['details'].append({
                    'period': str(period),
                    'month': period.month.strftime('%m/%Y'),
                    'status': 'error',
                    'expected': str(expected),
                    'actual': str(period.opening_balance),
                    'difference': str(diff),
                    'message': (
                        f'OPENING ERRADO: esperado {expected}, atual {period.opening_balance} '
                        f'(diff: {diff})'
                    ),
                })
            else:
                result['details'].append({
                    'period': str(period),
                    'month': period.month.strftime('%m/%Y'),
                    'status': 'ok',
                    'message': f'OK: {period.opening_balance}',
                })

        return result

    def _check_closing_balance(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}
        closed = period_qs.filter(status__in=['closed', 'archived'], closing_balance__isnull=False)

        for period in closed:
            net = self._calculate_net(period)
            expected = period.opening_balance + net
            diff = period.closing_balance - expected

            if diff != Decimal('0'):
                result['errors'] += 1
                result['details'].append({
                    'period': str(period),
                    'month': period.month.strftime('%m/%Y'),
                    'status': 'error',
                    'expected': str(expected),
                    'actual': str(period.closing_balance),
                    'difference': str(diff),
                    'opening': str(period.opening_balance),
                    'net': str(net),
                    'message': (
                        f'CLOSING ERRADO: opening({period.opening_balance}) + net({net}) = {expected}, '
                        f'mas esta {period.closing_balance} (diff: {diff})'
                    ),
                })
            else:
                result['details'].append({
                    'period': str(period),
                    'month': period.month.strftime('%m/%Y'),
                    'status': 'ok',
                    'message': f'OK: {period.closing_balance}',
                })

        if closed.count() == 0:
            result['warnings'] += 1
            result['details'].append({
                'status': 'warning',
                'message': 'Nenhum periodo fechado encontrado para verificar.',
            })

        return result

    def _check_monthly_report(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}
        periods = list(period_qs)

        for period in periods:
            report = MonthlyReportModel.objects.filter(month=period.month).first()
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

            if not report:
                if txs.exists():
                    result['warnings'] += 1
                    result['details'].append({
                        'period': str(period),
                        'month': period.month.strftime('%m/%Y'),
                        'status': 'warning',
                        'message': 'Sem MonthlyReportModel (periodo tem transacoes)',
                    })
                continue

            prev_period = period.get_previous_period()
            expected_prev_balance = Decimal('0.00')
            if prev_period:
                expected_prev_balance = prev_period.closing_balance or prev_period.opening_balance + self._calculate_net(prev_period)

            issues = []
            if report.previous_month_balance != expected_prev_balance:
                issues.append(f'previous_month_balance: esperado={expected_prev_balance}, atual={report.previous_month_balance}')
            if report.total_positive_transactions != positive:
                issues.append(f'total_positive: esperado={positive}, atual={report.total_positive_transactions}')
            if report.total_negative_transactions != negative:
                issues.append(f'total_negative: esperado={negative}, atual={report.total_negative_transactions}')
            if report.monthly_result != monthly_result:
                issues.append(f'monthly_result: esperado={monthly_result}, atual={report.monthly_result}')
            if report.total_balance != total_balance:
                issues.append(f'total_balance: esperado={total_balance}, atual={report.total_balance}')

            if issues:
                result['errors'] += 1
                result['details'].append({
                    'period': str(period),
                    'month': period.month.strftime('%m/%Y'),
                    'status': 'error',
                    'issues': issues,
                    'message': f'REPORT INCONSISTENTE: {"; ".join(issues)}',
                })
            else:
                result['details'].append({
                    'period': str(period),
                    'month': period.month.strftime('%m/%Y'),
                    'status': 'ok',
                    'message': 'OK',
                })

        return result

    def _check_period_gaps(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}
        all_periods = list(AccountingPeriod.objects.all().order_by('month'))

        if len(all_periods) < 2:
            result['details'].append({
                'status': 'info',
                'message': 'Menos de 2 periodos, impossivel verificar gaps.',
            })
            return result

        first = all_periods[0].month
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

        if gaps:
            result['warnings'] += len(gaps)
            for gap in gaps:
                result['details'].append({
                    'month': gap.strftime('%m/%Y'),
                    'status': 'warning',
                    'message': f'PERIODO FALTANTE: {gap.strftime("%m/%Y")}',
                })
        else:
            result['details'].append({
                'status': 'ok',
                'message': 'Nenhum gap encontrado.',
            })

        return result

    def _check_orphan_transactions(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}
        orphans = TransactionModel.objects.filter(accounting_period__isnull=True)

        for tx in orphans:
            result['errors'] += 1
            result['details'].append({
                'transaction_id': tx.id,
                'date': str(tx.date),
                'description': tx.description,
                'amount': str(tx.amount),
                'is_positive': tx.is_positive,
                'status': 'error',
                'message': f'ORFA: {tx.date} - {tx.description} - R$ {tx.amount}',
            })

        if not orphans.exists():
            result['details'].append({
                'status': 'ok',
                'message': 'Nenhuma transacao orfa encontrada.',
            })

        return result

    def _check_reversal_integrity(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}

        reversals = TransactionModel.objects.filter(transaction_type='reversal')
        for rev in reversals:
            if rev.reverses is None:
                result['errors'] += 1
                result['details'].append({
                    'transaction_id': rev.id,
                    'date': str(rev.date),
                    'status': 'error',
                    'message': f'ESTORNO SEM ORIGINAL: Transacao #{rev.id} ({rev.date}) e estorno mas nao aponta para nenhuma original.',
                })

        originals_reversed = TransactionModel.objects.filter(
            transaction_type='original',
            reversed_by__transaction_type='reversal',
        ).annotate(
            reversal_count=Count('reversed_by', filter=Q(reversed_by__transaction_type='reversal'))
        ).filter(reversal_count__gt=1)

        for orig in originals_reversed:
            result['errors'] += 1
            result['details'].append({
                'transaction_id': orig.id,
                'date': str(orig.date),
                'status': 'error',
                'message': f'ESTORNADA MAIS DE UMA VEZ: Transacao #{orig.id} ({orig.date}) possui multiplus estornos.',
            })

        reversals_pointing_to_reversals = TransactionModel.objects.filter(
            transaction_type='reversal',
            reverses__transaction_type='reversal',
        )
        for rev in reversals_pointing_to_reversals:
            result['errors'] += 1
            result['details'].append({
                'transaction_id': rev.id,
                'status': 'error',
                'message': f'ESTORNO DE ESTORNO: Transacao #{rev.id} estorna outra transacao que tambem e estorno.',
            })

        if result['errors'] == 0:
            result['details'].append({
                'status': 'ok',
                'message': 'Integridade de estornos OK.',
            })

        return result

    def _check_frozen_report_hash(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}
        reports = FrozenReport.objects.all()

        if not reports.exists():
            result['details'].append({
                'status': 'info',
                'message': 'Nenhum FrozenReport encontrado.',
            })
            return result

        for report in reports:
            try:
                verification = report.verify()
                if verification['valid']:
                    result['details'].append({
                        'report_id': str(report.id),
                        'type': report.report_type,
                        'period': str(report.period),
                        'status': 'ok',
                        'message': f'OK: {report.report_type} - {report.period}',
                    })
                else:
                    result['errors'] += 1
                    result['details'].append({
                        'report_id': str(report.id),
                        'type': report.report_type,
                        'period': str(report.period),
                        'stored_hash': verification['stored_hash'],
                        'current_hash': verification['current_hash'],
                        'status': 'error',
                        'message': f'HASH INVALIDO: {report.report_type} - {report.period}',
                    })
            except Exception as e:
                result['warnings'] += 1
                result['details'].append({
                    'report_id': str(report.id),
                    'type': report.report_type,
                    'period': str(report.period),
                    'status': 'warning',
                    'message': f'ERRO AO VERIFICAR: {e}',
                })

        return result

    def _check_first_month(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}
        first_months = AccountingPeriod.objects.filter(is_first_month=True)

        count = first_months.count()
        if count == 0:
            result['warnings'] += 1
            result['details'].append({
                'status': 'warning',
                'message': 'Nenhum periodo marcado como is_first_month=True.',
            })
        elif count == 1:
            fm = first_months.first()
            earliest = AccountingPeriod.objects.all().order_by('month').first()
            if earliest and fm.id != earliest.id:
                result['errors'] += 1
                result['details'].append({
                    'status': 'error',
                    'first_month': fm.month.strftime('%m/%Y'),
                    'earliest': earliest.month.strftime('%m/%Y'),
                    'message': (
                        f'is_first_month aponta para {fm.month.strftime("%m/%Y")} '
                        f'mas o periodo mais antigo e {earliest.month.strftime("%m/%Y")}'
                    ),
                })
            else:
                result['details'].append({
                    'status': 'ok',
                    'message': f'OK: Primeiro periodo em {fm.month.strftime("%m/%Y")}',
                })
        else:
            result['errors'] += 1
            months = ', '.join(fm.month.strftime('%m/%Y') for fm in first_months)
            result['details'].append({
                'status': 'error',
                'count': count,
                'months': months,
                'message': f'{count} periodos marcados como is_first_month: {months}. Deve ser apenas 1.',
            })

        return result

    def _check_running_balance(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}
        all_periods = list(AccountingPeriod.objects.all().order_by('month'))

        if not all_periods:
            result['details'].append({'status': 'info', 'message': 'Nenhum periodo encontrado.'})
            return result

        running = all_periods[0].opening_balance
        result['details'].append({
            'month': all_periods[0].month.strftime('%m/%Y'),
            'status': 'info',
            'running_balance': str(running),
            'message': f'Inicio: opening_balance = {running}',
        })

        for period in all_periods:
            net = self._calculate_net(period)
            expected_running = running + net
            actual_opening = period.opening_balance

            if actual_opening != running:
                result['errors'] += 1
                result['details'].append({
                    'month': period.month.strftime('%m/%Y'),
                    'status': 'error',
                    'expected_opening': str(running),
                    'actual_opening': str(actual_opening),
                    'difference': str(actual_opening - running),
                    'message': (
                        f'QUEBRA NA CADEIA: {period.month.strftime("%m/%Y")} '
                        f'opening esperado={running}, atual={actual_opening} '
                        f'(diff: {actual_opening - running})'
                    ),
                })

            running = actual_opening + net

            if period.closing_balance is not None and period.closing_balance != running:
                result['errors'] += 1
                result['details'].append({
                    'month': period.month.strftime('%m/%Y'),
                    'status': 'error',
                    'expected_closing': str(running),
                    'actual_closing': str(period.closing_balance),
                    'difference': str(period.closing_balance - running),
                    'message': (
                        f'CLOSING DIVERGENTE: {period.month.strftime("%m/%Y")} '
                        f'esperado={running}, atual={period.closing_balance} '
                        f'(diff: {period.closing_balance - running})'
                    ),
                })

        return result

    def _print_result(self, check_name, result):
        errors = result.get('errors', 0)
        warnings = result.get('warnings', 0)

        for detail in result.get('details', []):
            status = detail.get('status', 'info')
            msg = detail.get('message', '')

            if status == 'error':
                self.stdout.write(self.style.ERROR(f'  X {msg}'))
            elif status == 'warning':
                self.stdout.write(self.style.WARNING(f'  ! {msg}'))
            elif status == 'ok':
                self.stdout.write(self.style.SUCCESS(f'  OK {msg}'))
            else:
                self.stdout.write(f'  i {msg}')

        if errors > 0:
            self.stdout.write(self.style.ERROR(
                f'\n  -> {errors} erro(s) encontrado(s) nesta verificacao.'))
        elif warnings > 0:
            self.stdout.write(self.style.WARNING(
                f'\n  -> {warnings} aviso(s) nesta verificacao.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                '\n  -> Tudo OK nesta verificacao.'))

    def _check_amount_sign(self, period_qs):
        result = {'errors': 0, 'warnings': 0, 'details': []}

        old_style = TransactionModel.objects.filter(is_positive=False, amount__lt=0)
        new_style = TransactionModel.objects.filter(is_positive=False, amount__gt=0)
        positive_neg = TransactionModel.objects.filter(is_positive=True, amount__lt=0)

        old_count = old_style.count()
        new_count = new_style.count()
        positive_neg_count = positive_neg.count()

        if positive_neg_count > 0:
            result['errors'] += 1
            result['details'].append({
                'status': 'error',
                'count': positive_neg_count,
                'message': (
                    f'{positive_neg_count} transacoes com is_positive=True mas amount negativo!'
                    f' Isso e um dado corrompido.'
                ),
            })

        if old_count > 0 and new_count > 0:
            result['warnings'] += 1
            result['details'].append({
                'status': 'warning',
                'old_style_count': old_count,
                'new_style_count': new_count,
                'message': (
                    f'MISTURA DE PADROES: {old_count} transacoes com amount<0 (padrao antigo) '
                    f'e {new_count} com amount>0 (padrao novo) para is_positive=False. '
                    f'O sistema precisa normalizar isso.'
                ),
            })
            sample_old = old_style.first()
            sample_new = new_style.first()
            result['details'].append({
                'status': 'info',
                'message': (
                    f'  Exemplo antigo: ID={sample_old.id} amount={sample_old.amount} '
                    f'is_positive={sample_old.is_positive} ({sample_old.date})'
                ),
            })
            result['details'].append({
                'status': 'info',
                'message': (
                    f'  Exemplo novo: ID={sample_new.id} amount={sample_new.amount} '
                    f'is_positive={sample_new.is_positive} ({sample_new.date})'
                ),
            })
        elif old_count > 0:
            result['details'].append({
                'status': 'ok',
                'message': f'{old_count} transacoes negativas (padrao antigo: amount com sinal). Consistente.',
            })
        elif new_count > 0:
            result['details'].append({
                'status': 'ok',
                'message': f'{new_count} transacoes negativas (padrao novo: amount positivo + is_positive). Consistente.',
            })
        else:
            result['details'].append({
                'status': 'ok',
                'message': 'Nenhuma transacao negativa encontrada.',
            })

        return result
