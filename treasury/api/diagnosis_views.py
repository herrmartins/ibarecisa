import json
from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission

from django.db import models as db_models

from treasury.models import (
    AccountingPeriod,
    TransactionModel,
    ReversalTransaction,
    PeriodSnapshot,
    AuditLog,
    MonthlyReportModel,
    FrozenReport,
    CategoryModel,
)


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class DiagnosisView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request):
        report = {
            'generated_at': request.META.get('HTTP_DATE', ''),
            'summary': self._get_summary(),
            'periods': [],
            'issues': [],
            'snapshots': self._get_snapshots(),
            'audit_recent': self._get_recent_audit(),
        }
        report['periods'] = self._get_periods()
        report['issues'] = self._collect_issues(report['periods'])
        return Response(report)

    def _get_summary(self):
        periods = AccountingPeriod.objects.all()
        transactions = TransactionModel.objects.filter(transaction_type='original')
        orphans = TransactionModel.objects.filter(accounting_period__isnull=True)
        return {
            'total_periods': periods.count(),
            'open_periods': periods.filter(status='open').count(),
            'closed_periods': periods.filter(status='closed').count(),
            'archived_periods': periods.filter(status='archived').count(),
            'total_transactions': transactions.count(),
            'orphan_transactions': orphans.count(),
            'total_snapshots': PeriodSnapshot.objects.count(),
            'first_period': str(periods.order_by('month').first()) if periods.exists() else None,
            'last_period': str(periods.order_by('-month').first()) if periods.exists() else None,
        }

    def _get_periods(self):
        periods = AccountingPeriod.objects.all().order_by('month')
        result = []
        prev_period = None
        for period in periods:
            transactions = TransactionModel.objects.filter(
                accounting_period=period, transaction_type='original',
            )
            reversal_tx = TransactionModel.objects.filter(
                accounting_period=period, transaction_type='reversal',
            )
            reversals = ReversalTransaction.objects.filter(
                db_models.Q(original_transaction__accounting_period=period)
                | db_models.Q(reversal_transaction__accounting_period=period)
            )

            positive = transactions.filter(is_positive=True, amount__gt=0).aggregate(
                t=db_models.Sum('amount')
            )['t'] or Decimal('0.00')
            neg_new = transactions.filter(is_positive=False, amount__gt=0).aggregate(
                t=db_models.Sum('amount')
            )['t'] or Decimal('0.00')
            neg_old = transactions.filter(is_positive=False, amount__lt=0).aggregate(
                t=db_models.Sum('amount')
            )['t'] or Decimal('0.00')
            net = positive + neg_old - neg_new

            pd = {
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
                'reversal_count': reversal_tx.count(),
                'total_positive': float(positive),
                'total_negative_new': float(neg_new),
                'total_negative_old': float(neg_old),
                'net': float(net),
                'calculated_balance': float(period.opening_balance + net),
                'has_monthly_report': MonthlyReportModel.objects.filter(month=period.month).exists(),
                'has_frozen_report': FrozenReport.objects.filter(period=period).exists(),
                'issues': [],
                'chain_ok': True,
            }

            if prev_period and prev_period.closing_balance is not None:
                if period.opening_balance != prev_period.closing_balance:
                    pd['chain_ok'] = False
                    pd['issues'].append({
                        'severity': 'error', 'type': 'chain_broken',
                        'message': f'opening ({period.opening_balance}) != closing anterior ({prev_period.closing_balance})',
                    })

            if period.status == 'closed' and period.closing_balance is not None:
                calculated = period.opening_balance + net
                if abs(period.closing_balance - calculated) > Decimal('0.01'):
                    pd['issues'].append({
                        'severity': 'error', 'type': 'closing_mismatch',
                        'message': f'closing ({period.closing_balance}) != calculado ({calculated})',
                    })

            has_old = transactions.filter(is_positive=False, amount__lt=0).exists()
            has_new = transactions.filter(is_positive=False, amount__gt=0).exists()
            if has_old and has_new:
                pd['issues'].append({
                    'severity': 'warning', 'type': 'mixed_sign',
                    'message': 'Mistura de padrões de sinal',
                })

            linked_wrong = TransactionModel.objects.filter(
                date__year=period.month.year,
                date__month=period.month.month,
            ).exclude(accounting_period=period).exclude(accounting_period__isnull=True)
            if linked_wrong.exists():
                pd['issues'].append({
                    'severity': 'warning', 'type': 'wrong_link',
                    'message': f'{linked_wrong.count()} transações com data aqui vinculadas a outro período',
                })

            result.append(pd)
            prev_period = period

        return result

    def _collect_issues(self, periods_data):
        issues = []
        orphans = TransactionModel.objects.filter(accounting_period__isnull=True)
        if orphans.exists():
            issues.append({
                'severity': 'error', 'type': 'orphan_transactions',
                'message': f'{orphans.count()} transações sem período',
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


class DiagnosisSnapshotView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request):
        period_id = request.data.get('period_id')
        reason = request.data.get('reason', '')

        if not period_id:
            return Response({'error': 'period_id obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            period = AccountingPeriod.objects.get(id=period_id)
        except AccountingPeriod.DoesNotExist:
            return Response({'error': 'Período não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if not reason:
            reason = f'Snapshot via dashboard - {period.month_name}/{period.year}'

        snapshot = PeriodSnapshot.create_from_period(
            period, created_by=request.user, reason=reason,
        )

        AuditLog.log(
            action='snapshot_created', entity_type='AccountingPeriod',
            entity_id=period.id, user=request.user,
            new_values={
                'snapshot_id': str(snapshot.id),
                'period_status': period.status,
                'transactions_count': snapshot.transactions_count,
            },
            description=f'Snapshot criado via dashboard: {reason}',
            period_id=period.id,
        )

        return Response({
            'snapshot_id': str(snapshot.id),
            'period_label': f'{period.month_name}/{period.year}',
            'transactions_count': snapshot.transactions_count,
        })


class DiagnosisRestoreView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request):
        snapshot_id = request.data.get('snapshot_id')
        if not snapshot_id:
            return Response({'error': 'snapshot_id obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            snapshot = PeriodSnapshot.objects.get(id=snapshot_id)
        except PeriodSnapshot.DoesNotExist:
            return Response({'error': 'Snapshot não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        try:
            period = AccountingPeriod.objects.get(id=snapshot.period_id)
        except AccountingPeriod.DoesNotExist:
            return Response({'error': 'Período não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        pre_snapshot = PeriodSnapshot.create_from_period(
            period, created_by=request.user,
            reason=f'Auto-snapshot antes de restore via dashboard',
        )

        ReversalTransaction.objects.filter(
            original_transaction__accounting_period=period,
        ).delete()
        ReversalTransaction.objects.filter(
            reversal_transaction__accounting_period=period,
        ).delete()

        TransactionModel.objects.filter(accounting_period=period).delete()
        MonthlyReportModel.objects.filter(month=period.month).delete()
        FrozenReport.objects.filter(period=period).delete()

        snap_txs = snapshot.snapshot_data.get('transactions', [])
        restored = 0
        for tx_data in snap_txs:
            try:
                category = None
                if tx_data.get('category'):
                    category = CategoryModel.objects.filter(name=tx_data['category']).first()

                TransactionModel.objects.create(
                    user=request.user,
                    created_by=request.user,
                    accounting_period=period,
                    description=tx_data.get('description', ''),
                    amount=Decimal(str(tx_data.get('amount', 0))),
                    is_positive=tx_data.get('is_positive', True),
                    date=date.fromisoformat(tx_data['date']),
                    category=category,
                    transaction_type='original',
                )
                restored += 1
            except Exception:
                pass

        snap_summary = snapshot.snapshot_data.get('summary', {})
        if snap_summary.get('opening_balance') is not None:
            period.opening_balance = Decimal(str(snap_summary['opening_balance']))
            period.save(update_fields=['opening_balance'])

        AuditLog.log(
            action='period_restored', entity_type='AccountingPeriod',
            entity_id=period.id, user=request.user,
            old_values={'pre_restore_snapshot': str(pre_snapshot.id)},
            new_values={
                'from_snapshot': str(snapshot.id),
                'restored_transactions': restored,
            },
            description=f'Restore via dashboard: {restored} transações restauradas',
            period_id=period.id,
        )

        return Response({
            'restored_transactions': restored,
            'pre_restore_snapshot_id': str(pre_snapshot.id),
            'message': f'{restored} transações restauradas com sucesso',
        })


class DiagnosisReopenView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request):
        period_id = request.data.get('period_id')
        reason = request.data.get('reason', 'Reabertura via dashboard')

        if not period_id:
            return Response({'error': 'period_id obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            period = AccountingPeriod.objects.get(id=period_id)
        except AccountingPeriod.DoesNotExist:
            return Response({'error': 'Período não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if period.status == 'open':
            return Response({'error': 'Período já está aberto'}, status=status.HTTP_400_BAD_REQUEST)

        snapshot = PeriodSnapshot.create_from_period(
            period, created_by=request.user,
            reason=f'Auto-snapshot antes de reabertura: {reason}',
        )

        period.status = 'open'
        old_closing = period.closing_balance
        period.closing_balance = None
        period.closed_at = None
        period.closed_by = None
        period.notes = ''
        period.save(update_fields=['status', 'closing_balance', 'closed_at', 'closed_by', 'notes'])

        MonthlyReportModel.objects.filter(month=period.month).delete()

        AuditLog.log(
            action='period_reopened', entity_type='AccountingPeriod',
            entity_id=period.id, user=request.user,
            old_values={
                'old_status': 'closed/archived',
                'old_closing_balance': float(old_closing) if old_closing else None,
                'snapshot_id': str(snapshot.id),
            },
            new_values={'status': 'open'},
            description=f'Reabertura via dashboard: {reason}',
            period_id=period.id,
        )

        return Response({
            'snapshot_id': str(snapshot.id),
            'period_label': f'{period.month_name}/{period.year}',
            'old_closing_balance': float(old_closing) if old_closing else None,
            'message': f'Período {period.month_name}/{period.year} reaberto com sucesso',
        })
