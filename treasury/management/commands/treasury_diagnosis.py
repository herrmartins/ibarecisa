import json
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import models as db_models
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


class Command(BaseCommand):
    help = 'Diagnóstico completo da tesouraria - relatório do estado atual'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', type=str, default='terminal',
            choices=['terminal', 'json'],
            help='Formato de saída: terminal (padrão) ou json',
        )
        parser.add_argument(
            '--json-file', type=str, default='',
            help='Arquivo para salvar JSON (apenas com --output json)',
        )

    def handle(self, *args, **options):
        output_format = options['output']
        json_file = options.get('json_file', '')

        report = {
            'generated_at': timezone.now().isoformat(),
            'summary': self._get_summary(),
            'periods': self._get_periods_diagnosis(),
            'issues': [],
            'snapshots': self._get_snapshots(),
            'audit_recent': self._get_recent_audit(),
        }

        report['issues'] = self._collect_issues(report['periods'])

        if output_format == 'json':
            json_str = json.dumps(report, indent=2, default=str, ensure_ascii=False)
            if json_file:
                with open(json_file, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                self.stdout.write(self.style.SUCCESS(f'JSON salvo em {json_file}'))
            else:
                self.stdout.write(json_str)
        else:
            self._print_terminal_report(report)

    def _get_summary(self):
        periods = AccountingPeriod.objects.all()
        transactions = TransactionModel.objects.filter(transaction_type='original')
        open_periods = periods.filter(status='open')
        closed_periods = periods.filter(status='closed')
        archived_periods = periods.filter(status='archived')

        orphans = TransactionModel.objects.filter(accounting_period__isnull=True)

        return {
            'total_periods': periods.count(),
            'open_periods': open_periods.count(),
            'closed_periods': closed_periods.count(),
            'archived_periods': archived_periods.count(),
            'total_transactions': transactions.count(),
            'orphan_transactions': orphans.count(),
            'total_snapshots': PeriodSnapshot.objects.count(),
            'first_period': str(periods.order_by('month').first()) if periods.exists() else None,
            'last_period': str(periods.order_by('-month').first()) if periods.exists() else None,
        }

    def _get_periods_diagnosis(self):
        periods = AccountingPeriod.objects.all().order_by('month')
        result = []

        prev_period = None
        for period in periods:
            transactions = TransactionModel.objects.filter(
                accounting_period=period,
                transaction_type='original',
            )
            reversal_tx = TransactionModel.objects.filter(
                accounting_period=period,
                transaction_type='reversal',
            )
            reversals = ReversalTransaction.objects.filter(
                db_models.Q(original_transaction__accounting_period=period)
                | db_models.Q(reversal_transaction__accounting_period=period)
            )

            positive = transactions.filter(is_positive=True, amount__gt=0).aggregate(
                total=db_models.Sum('amount')
            )['total'] or Decimal('0.00')

            negative_new = transactions.filter(is_positive=False, amount__gt=0).aggregate(
                total=db_models.Sum('amount')
            )['total'] or Decimal('0.00')

            negative_old = transactions.filter(is_positive=False, amount__lt=0).aggregate(
                total=db_models.Sum('amount')
            )['total'] or Decimal('0.00')

            net = positive + negative_old - negative_new

            period_data = {
                'id': period.id,
                'month': str(period.month),
                'month_label': f'{period.month_name}/{period.year}',
                'status': period.status,
                'is_first_month': period.is_first_month,
                'opening_balance': float(period.opening_balance),
                'closing_balance': float(period.closing_balance) if period.closing_balance else None,
                'closed_at': period.closed_at.isoformat() if period.closed_at else None,
                'closed_by': str(period.closed_by) if period.closed_by else None,
                'transactions_count': transactions.count(),
                'reversal_transactions_count': reversal_tx.count(),
                'reversals_count': reversals.count(),
                'total_positive': float(positive),
                'total_negative_new': float(negative_new),
                'total_negative_old': float(negative_old),
                'net': float(net),
                'calculated_balance': float(period.opening_balance + net),
                'has_monthly_report': MonthlyReportModel.objects.filter(month=period.month).exists(),
                'has_frozen_report': FrozenReport.objects.filter(period=period).exists(),
                'issues': [],
            }

            chain_ok = True
            if prev_period:
                if prev_period.closing_balance is not None:
                    expected_opening = prev_period.closing_balance
                    if period.opening_balance != expected_opening:
                        chain_ok = False
                        period_data['issues'].append({
                            'severity': 'error',
                            'type': 'chain_broken',
                            'message': (
                                f'opening_balance ({period.opening_balance}) != '
                                f'closing_balance anterior ({expected_opening})'
                            ),
                        })
                elif prev_period.status == 'closed' and prev_period.closing_balance is None:
                    period_data['issues'].append({
                        'severity': 'warning',
                        'type': 'missing_closing_balance',
                        'message': 'Período anterior está fechado mas sem closing_balance',
                    })

            period_data['chain_ok'] = chain_ok

            if period.status == 'closed' and period.closing_balance is not None:
                calculated = period.opening_balance + net
                if abs(period.closing_balance - calculated) > Decimal('0.01'):
                    period_data['issues'].append({
                        'severity': 'error',
                        'type': 'closing_balance_mismatch',
                        'message': (
                            f'closing_balance ({period.closing_balance}) != '
                            f'opening + net ({calculated})'
                        ),
                    })

            has_old_pattern = transactions.filter(is_positive=False, amount__lt=0).exists()
            has_new_pattern = transactions.filter(is_positive=False, amount__gt=0).exists()
            if has_old_pattern and has_new_pattern:
                period_data['issues'].append({
                    'severity': 'warning',
                    'type': 'mixed_sign_pattern',
                    'message': 'Mistura de padrões de sinal em transações negativas',
                })

            linked_wrong = TransactionModel.objects.filter(
                date__year=period.month.year,
                date__month=period.month.month,
            ).exclude(accounting_period=period).exclude(accounting_period__isnull=True)

            if linked_wrong.exists():
                period_data['issues'].append({
                    'severity': 'warning',
                    'type': 'transactions_linked_elsewhere',
                    'message': (
                        f'{linked_wrong.count()} transações com data neste mês '
                        f'estão vinculadas a outro período'
                    ),
                })

            result.append(period_data)
            prev_period = period

        if result and not any(p.get('is_first_month') for p in result):
            result[0]['issues'].append({
                'severity': 'warning',
                'type': 'no_first_month',
                'message': 'Nenhum período marcado como is_first_month',
            })

        self._check_gaps(result)

        return result

    def _check_gaps(self, periods_data):
        if len(periods_data) < 2:
            return
        for i in range(1, len(periods_data)):
            prev_date = date.fromisoformat(periods_data[i - 1]['month'])
            curr_date = date.fromisoformat(periods_data[i]['month'])
            expected_next = None
            if prev_date.month == 12:
                expected_next = date(prev_date.year + 1, 1, 1)
            else:
                expected_next = date(prev_date.year, prev_date.month + 1, 1)
            if curr_date != expected_next:
                gap_start = expected_next
                gap_end_month = curr_date.month - 1 if curr_date.month > 1 else 12
                gap_end_year = curr_date.year if curr_date.month > 1 else curr_date.year - 1
                periods_data[i]['issues'].append({
                    'severity': 'warning',
                    'type': 'period_gap',
                    'message': (
                        f'Gap entre {gap_start.strftime("%m/%Y")} e '
                        f'{curr_date.strftime("%m/%Y")}'
                    ),
                })

    def _collect_issues(self, periods_data):
        issues = []
        orphans = TransactionModel.objects.filter(accounting_period__isnull=True)
        if orphans.exists():
            issues.append({
                'severity': 'error',
                'type': 'orphan_transactions',
                'message': f'{orphans.count()} transações sem accounting_period',
                'transaction_ids': list(orphans.values_list('id', flat=True)[:50]),
            })

        for pd in periods_data:
            for issue in pd.get('issues', []):
                issue['period'] = pd['month_label']
                issues.append(issue)

        issues.sort(key=lambda x: 0 if x['severity'] == 'error' else 1)
        return issues

    def _get_snapshots(self):
        snapshots = PeriodSnapshot.objects.all().order_by('-created_at')[:20]
        return [
            {
                'id': str(s.id),
                'period_month': s.period_month,
                'period_year': s.period_year,
                'period_label': f'{s.period_month:02d}/{s.period_year}',
                'created_at': s.created_at.isoformat(),
                'created_by': s.created_by_name or '-',
                'reason': s.reason,
                'transactions_count': s.transactions_count,
                'closing_balance': float(s.closing_balance) if s.closing_balance else None,
                'was_closed': s.was_closed,
            }
            for s in snapshots
        ]

    def _get_recent_audit(self):
        try:
            logs = AuditLog.objects.filter(
                entity_type__in=['AccountingPeriod', 'TransactionModel']
            ).order_by('-timestamp')[:30]
            return [
                {
                    'id': str(log.id),
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.action,
                    'user_name': log.user_name or '-',
                    'entity_type': log.entity_type,
                    'entity_id': log.entity_id,
                    'description': log.description,
                }
                for log in logs
            ]
        except Exception:
            return []

    def _print_terminal_report(self, report):
        summary = report['summary']

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('  DIAGNÓSTICO DA TESOURARIA'))
        self.stdout.write(f'  Gerado em: {timezone.now().strftime("%d/%m/%Y %H:%M")}')
        self.stdout.write('=' * 70)

        self.stdout.write(f'\n  Resumo:')
        self.stdout.write(f'    Períodos: {summary["total_periods"]} '
                          f'({summary["open_periods"]} abertos, '
                          f'{summary["closed_periods"]} fechados, '
                          f'{summary["archived_periods"]} arquivados)')
        self.stdout.write(f'    Transações: {summary["total_transactions"]} '
                          f'({summary["orphan_transactions"]} órfãs)')
        self.stdout.write(f'    Snapshots: {summary["total_snapshots"]}')
        self.stdout.write(f'    Período inicial: {summary["first_period"]}')
        self.stdout.write(f'    Período final: {summary["last_period"]}')

        self.stdout.write(f'\n  Períodos:')
        self.stdout.write('  ' + '-' * 66)
        self.stdout.write(f'  {"Mês":<14} {"Status":<10} {"Abertura":>12} {"Fechamento":>12} {"Tx":>5} {"Cadeia":>8}')
        self.stdout.write('  ' + '-' * 66)

        for pd in report['periods']:
            status_colors = {
                'open': self.style.SUCCESS,
                'closed': self.style.WARNING,
                'archived': self.style.NOTICE,
            }
            color_fn = status_colors.get(pd['status'], str)
            chain_str = 'OK' if pd['chain_ok'] else 'QUEBRADA'
            closing_str = f'{pd["closing_balance"]:.2f}' if pd['closing_balance'] is not None else '-'
            self.stdout.write(
                f'  {pd["month_label"]:<14} '
                f'{color_fn(pd["status"]):<10} '
                f'{pd["opening_balance"]:>12.2f} '
                f'{closing_str:>12} '
                f'{pd["transactions_count"]:>5} '
                f'{chain_str:>8}'
            )

        if report['issues']:
            self.stdout.write(f'\n  Problemas encontrados ({len(report["issues"])}):')
            for issue in report['issues']:
                severity_str = 'ERRO' if issue['severity'] == 'error' else 'AVISO'
                period_str = f'[{issue.get("period", "?")}] ' if 'period' in issue else ''
                fn = self.style.ERROR if issue['severity'] == 'error' else self.style.WARNING
                self.stdout.write(f'    {fn(severity_str)} {period_str}{issue["message"]}')
        else:
            self.stdout.write(self.style.SUCCESS('\n  Nenhum problema encontrado!'))

        if report['snapshots']:
            self.stdout.write(f'\n  Últimos snapshots ({len(report["snapshots"])}):')
            for snap in report['snapshots'][:5]:
                self.stdout.write(
                    f'    {snap["period_label"]} | {snap["created_at"][:16]} | '
                    f'{snap["created_by"]} | {snap["transactions_count"]} tx | '
                    f'{snap["reason"][:50]}'
                )

        self.stdout.write('\n' + '=' * 70 + '\n')
