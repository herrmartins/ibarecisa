from datetime import date
from decimal import Decimal
from io import StringIO
import json

from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from users.models import CustomUser
from treasury.models import (
    AccountingPeriod,
    TransactionModel,
    CategoryModel,
    PeriodSnapshot,
    AuditLog,
    ReversalTransaction,
    MonthlyReportModel,
)


class DiagnosisTestBase(APITestCase):
    databases = ['default', 'audit']

    def setUp(self):
        self.superuser = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123',
        )
        self.treasurer = CustomUser.objects.create_user(
            username='treasurer',
            email='treasurer@test.com',
            password='testpass123',
            is_treasurer=True,
            type=CustomUser.Types.STAFF,
        )
        self.regular_user = CustomUser.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123',
            type=CustomUser.Types.REGULAR,
        )
        self.category = CategoryModel.objects.create(name='Dizimos')

        self.period_open = AccountingPeriod.objects.create(
            month=date(2025, 1, 1),
            opening_balance=Decimal('1000.00'),
            status='open',
        )
        self.period_closed = AccountingPeriod.objects.create(
            month=date(2025, 2, 1),
            opening_balance=Decimal('1000.00'),
            status='closed',
            closing_balance=Decimal('1200.00'),
            closed_by=self.superuser,
        )
        self.period_archived = AccountingPeriod.objects.create(
            month=date(2024, 12, 1),
            opening_balance=Decimal('500.00'),
            status='archived',
            closing_balance=Decimal('1000.00'),
            closed_by=self.superuser,
        )

        self.tx_open = TransactionModel.objects.create(
            user=self.treasurer,
            category=self.category,
            description='Transacao aberta',
            amount=Decimal('100.00'),
            is_positive=True,
            date=date(2025, 1, 15),
            accounting_period=self.period_open,
            created_by=self.treasurer,
        )
        self.tx_closed = TransactionModel.objects.create(
            user=self.treasurer,
            category=self.category,
            description='Transacao fechada',
            amount=Decimal('200.00'),
            is_positive=True,
            date=date(2025, 2, 15),
            accounting_period=self.period_closed,
            created_by=self.treasurer,
        )
        self.tx_archived = TransactionModel.objects.create(
            user=self.treasurer,
            category=self.category,
            description='Transacao arquivada',
            amount=Decimal('300.00'),
            is_positive=True,
            date=date(2024, 12, 15),
            accounting_period=self.period_archived,
            created_by=self.treasurer,
        )

        self.api_client = APIClient()


class SerializerBugFixTests(DiagnosisTestBase):
    def test_update_serializer_blocks_closed_period(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.patch(
            f'/treasury/api/transactions/{self.tx_closed.pk}/',
            {'description': 'Tentativa de edicao'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_serializer_blocks_archived_period(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.patch(
            f'/treasury/api/transactions/{self.tx_archived.pk}/',
            {'description': 'Tentativa de edicao'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_serializer_allows_open_period(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.patch(
            f'/treasury/api/transactions/{self.tx_open.pk}/',
            {'description': 'Edicao permitida'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_destroy_blocks_closed_period(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.delete(
            f'/treasury/api/transactions/{self.tx_closed.pk}/',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_blocks_archived_period(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.delete(
            f'/treasury/api/transactions/{self.tx_archived.pk}/',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_allows_open_period(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.delete(
            f'/treasury/api/transactions/{self.tx_open.pk}/',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_serializer_includes_can_be_reversed(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.get('/treasury/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data if isinstance(data, list) else data.get('results', [])
        self.assertTrue(len(results) > 0)
        tx = results[0]
        self.assertIn('can_be_reversed', tx)

    def test_list_serializer_includes_can_be_deleted(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.get('/treasury/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data if isinstance(data, list) else data.get('results', [])
        self.assertTrue(len(results) > 0)
        tx = results[0]
        self.assertIn('can_be_deleted', tx)

    def test_list_serializer_can_be_reversed_true_for_closed(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.get('/treasury/api/transactions/')
        data = response.json()
        results = data if isinstance(data, list) else data.get('results', [])
        closed_tx = [t for t in results if t.get('period_status') == 'closed']
        if closed_tx:
            self.assertTrue(closed_tx[0]['can_be_reversed'])
            self.assertFalse(closed_tx[0]['can_be_edited'])

    def test_list_serializer_can_be_edited_true_for_open(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.get('/treasury/api/transactions/')
        data = response.json()
        results = data if isinstance(data, list) else data.get('results', [])
        open_tx = [t for t in results if t.get('period_status') == 'open']
        if open_tx:
            self.assertTrue(open_tx[0]['can_be_edited'])
            self.assertFalse(open_tx[0]['can_be_reversed'])


class DiagnosisCommandTests(DiagnosisTestBase):
    def test_diagnosis_runs_without_error(self):
        out = StringIO()
        call_command('treasury_diagnosis', stdout=out)
        output = out.getvalue()
        self.assertIn('DIAGN', output)

    def test_diagnosis_shows_all_periods(self):
        out = StringIO()
        call_command('treasury_diagnosis', stdout=out)
        output = out.getvalue()
        self.assertIn('Janeiro/2025', output)
        self.assertIn('Fevereiro/2025', output)
        self.assertIn('Dezembro/2024', output)

    def test_diagnosis_json_output(self):
        out = StringIO()
        call_command('treasury_diagnosis', '--output', 'json', stdout=out)
        data = json.loads(out.getvalue())
        self.assertIn('summary', data)
        self.assertIn('periods', data)
        self.assertIn('issues', data)
        self.assertIn('snapshots', data)
        self.assertIn('audit_recent', data)

    def test_diagnosis_json_file_output(self):
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            filepath = f.name
        try:
            call_command('treasury_diagnosis', '--output', 'json', '--json-file', filepath)
            with open(filepath) as f:
                data = json.load(f)
            self.assertIn('summary', data)
            self.assertEqual(data['summary']['total_periods'], 3)
        finally:
            os.unlink(filepath)

    def test_diagnosis_detects_chain_break(self):
        self.period_open.opening_balance = Decimal('9999.00')
        AccountingPeriod.objects.filter(pk=self.period_open.pk).update(
            opening_balance=Decimal('9999.00'),
        )

        out = StringIO()
        call_command('treasury_diagnosis', '--output', 'json', stdout=out)
        data = json.loads(out.getvalue())
        chain_issues = [i for i in data['issues'] if i.get('type') == 'chain_broken']
        self.assertTrue(len(chain_issues) > 0)

    def test_diagnosis_no_issues_when_consistent(self):
        self.period_archived.status = 'closed'
        AccountingPeriod.objects.filter(pk=self.period_archived.pk).update(status='closed')

        out = StringIO()
        call_command('treasury_diagnosis', '--output', 'json', stdout=out)
        data = json.loads(out.getvalue())
        chain_issues = [i for i in data['issues'] if i.get('type') == 'chain_broken']
        self.assertEqual(len(chain_issues), 0)

    def test_diagnosis_summary_counts(self):
        out = StringIO()
        call_command('treasury_diagnosis', '--output', 'json', stdout=out)
        data = json.loads(out.getvalue())
        self.assertEqual(data['summary']['total_periods'], 3)
        self.assertEqual(data['summary']['open_periods'], 1)
        self.assertEqual(data['summary']['closed_periods'], 1)
        self.assertEqual(data['summary']['archived_periods'], 1)


class SnapshotCommandTests(DiagnosisTestBase):
    def test_snapshot_creates_period_snapshot(self):
        out = StringIO()
        call_command(
            'snapshot_period',
            '--month', '01/2025',
            '--user-id', str(self.superuser.pk),
            '--reason', 'Test snapshot',
            stdout=out,
        )
        self.assertTrue(PeriodSnapshot.objects.filter(
            period_month=1,
            period_year=2025,
        ).exists())

    def test_snapshot_records_transactions(self):
        out = StringIO()
        call_command(
            'snapshot_period',
            '--month', '01/2025',
            '--user-id', str(self.superuser.pk),
            stdout=out,
        )
        snap = PeriodSnapshot.objects.filter(period_month=1, period_year=2025).first()
        self.assertIsNotNone(snap)
        self.assertEqual(snap.transactions_count, 1)
        snap_data = snap.snapshot_data
        self.assertTrue(len(snap_data.get('transactions', [])) > 0)

    def test_snapshot_invalid_format(self):
        with self.assertRaises(Exception):
            call_command('snapshot_period', '--month', 'invalid', stderr=StringIO())

    def test_snapshot_nonexistent_period(self):
        with self.assertRaises(Exception):
            call_command('snapshot_period', '--month', '06/2030', stderr=StringIO())


class RestoreCommandTests(DiagnosisTestBase):
    def _create_snapshot(self):
        out = StringIO()
        call_command(
            'snapshot_period',
            '--month', '01/2025',
            '--user-id', str(self.superuser.pk),
            '--reason', 'Before restore test',
            stdout=out,
        )
        return PeriodSnapshot.objects.filter(period_month=1, period_year=2025).first()

    def test_restore_dry_run_does_not_alter(self):
        snap = self._create_snapshot()
        self.assertIsNotNone(snap)

        original_count = TransactionModel.objects.filter(
            accounting_period=self.period_open,
        ).count()

        out = StringIO()
        call_command(
            'restore_period',
            '--snapshot-id', str(snap.id),
            '--dry-run',
            stdout=out,
        )

        after_count = TransactionModel.objects.filter(
            accounting_period=self.period_open,
        ).count()
        self.assertEqual(original_count, after_count)

    def test_restore_recreates_transactions(self):
        snap = self._create_snapshot()
        self.assertIsNotNone(snap)

        TransactionModel.objects.filter(accounting_period=self.period_open).delete()
        self.assertEqual(
            TransactionModel.objects.filter(accounting_period=self.period_open).count(), 0,
        )

        out = StringIO()
        call_command(
            'restore_period',
            '--snapshot-id', str(snap.id),
            '--user-id', str(self.superuser.pk),
            '--no-confirm',
            stdout=out,
        )

        self.assertEqual(
            TransactionModel.objects.filter(
                accounting_period=self.period_open,
                transaction_type='original',
            ).count(), 1,
        )

    def test_restore_creates_pre_snapshot(self):
        snap = self._create_snapshot()
        self.assertIsNotNone(snap)

        existing_snaps = PeriodSnapshot.objects.count()

        out = StringIO()
        call_command(
            'restore_period',
            '--snapshot-id', str(snap.id),
            '--user-id', str(self.superuser.pk),
            '--no-confirm',
            stdout=out,
        )

        self.assertEqual(PeriodSnapshot.objects.count(), existing_snaps + 1)

    def test_restore_nonexistent_snapshot(self):
        with self.assertRaises(Exception):
            call_command(
                'restore_period',
                '--snapshot-id', '00000000-0000-0000-0000-000000000000',
                stderr=StringIO(),
            )


class DiagnosisAPITests(DiagnosisTestBase):
    def test_diagnosis_api_superuser_access(self):
        self.api_client.force_authenticate(user=self.superuser)
        response = self.api_client.get('/treasury/api/diagnosis/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_diagnosis_api_non_superuser_blocked(self):
        self.api_client.force_authenticate(user=self.treasurer)
        response = self.api_client.get('/treasury/api/diagnosis/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_diagnosis_api_unauthenticated_blocked(self):
        self.api_client.force_authenticate(user=None)
        response = self.api_client.get('/treasury/api/diagnosis/')
        self.assertIn(response.status_code, [401, 403])

    def test_diagnosis_api_returns_report_structure(self):
        self.api_client.force_authenticate(user=self.superuser)
        response = self.api_client.get('/treasury/api/diagnosis/')
        data = response.json()
        self.assertIn('summary', data)
        self.assertIn('periods', data)
        self.assertIn('issues', data)
        self.assertIn('snapshots', data)
        self.assertIn('audit_recent', data)

    def test_diagnosis_api_summary_counts(self):
        self.api_client.force_authenticate(user=self.superuser)
        response = self.api_client.get('/treasury/api/diagnosis/')
        data = response.json()
        self.assertEqual(data['summary']['total_periods'], 3)

    def test_snapshot_api_creates_snapshot(self):
        self.api_client.force_authenticate(user=self.superuser)
        response = self.api_client.post(
            '/treasury/api/diagnosis/snapshot/',
            {'period_id': self.period_open.pk, 'reason': 'API test'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('snapshot_id', data)
        self.assertTrue(PeriodSnapshot.objects.filter(id=data['snapshot_id']).exists())

    def test_snapshot_api_missing_period_id(self):
        self.api_client.force_authenticate(user=self.superuser)
        response = self.api_client.post('/treasury/api/diagnosis/snapshot/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reopen_api_reopens_period(self):
        self.api_client.force_authenticate(user=self.superuser)
        response = self.api_client.post(
            '/treasury/api/diagnosis/reopen/',
            {'period_id': self.period_closed.pk, 'reason': 'Reopen test'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.period_closed.refresh_from_db()
        self.assertEqual(self.period_closed.status, 'open')
        self.assertIsNone(self.period_closed.closing_balance)

    def test_reopen_api_creates_snapshot(self):
        existing = PeriodSnapshot.objects.count()
        self.api_client.force_authenticate(user=self.superuser)
        self.api_client.post(
            '/treasury/api/diagnosis/reopen/',
            {'period_id': self.period_closed.pk},
            format='json',
        )
        self.assertEqual(PeriodSnapshot.objects.count(), existing + 1)

    def test_reopen_api_blocks_already_open(self):
        self.api_client.force_authenticate(user=self.superuser)
        response = self.api_client.post(
            '/treasury/api/diagnosis/reopen/',
            {'period_id': self.period_open.pk},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restore_api_restores_period(self):
        self.api_client.force_authenticate(user=self.superuser)
        snap_resp = self.api_client.post(
            '/treasury/api/diagnosis/snapshot/',
            {'period_id': self.period_open.pk},
            format='json',
        )
        snapshot_id = snap_resp.json()['snapshot_id']

        TransactionModel.objects.filter(accounting_period=self.period_open).delete()

        restore_resp = self.api_client.post(
            '/treasury/api/diagnosis/restore/',
            {'snapshot_id': snapshot_id},
            format='json',
        )
        self.assertEqual(restore_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            TransactionModel.objects.filter(
                accounting_period=self.period_open,
                transaction_type='original',
            ).count(), 1,
        )

    def test_restore_api_creates_pre_snapshot(self):
        self.api_client.force_authenticate(user=self.superuser)
        snap_resp = self.api_client.post(
            '/treasury/api/diagnosis/snapshot/',
            {'period_id': self.period_open.pk},
            format='json',
        )
        snapshot_id = snap_resp.json()['snapshot_id']

        existing = PeriodSnapshot.objects.count()

        self.api_client.post(
            '/treasury/api/diagnosis/restore/',
            {'snapshot_id': snapshot_id},
            format='json',
        )

        self.assertEqual(PeriodSnapshot.objects.count(), existing + 1)

    def test_restore_api_missing_snapshot_id(self):
        self.api_client.force_authenticate(user=self.superuser)
        response = self.api_client.post('/treasury/api/diagnosis/restore/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DiagnosisTemplateViewTests(DiagnosisTestBase):
    def test_diagnosis_page_superuser_access(self):
        from django.test import Client
        client = Client()
        client.force_login(self.superuser)
        response = client.get('/treasury/admin/diagnostico/')
        self.assertEqual(response.status_code, 200)

    def test_diagnosis_page_non_superuser_blocked(self):
        from django.test import Client
        client = Client()
        client.force_login(self.treasurer)
        response = client.get('/treasury/admin/diagnostico/')
        self.assertEqual(response.status_code, 403)

    def test_diagnosis_page_regular_user_blocked(self):
        from django.test import Client
        client = Client()
        client.force_login(self.regular_user)
        response = client.get('/treasury/admin/diagnostico/')
        self.assertEqual(response.status_code, 403)
