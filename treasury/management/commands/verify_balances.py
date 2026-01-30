"""
Management Command para verificação e reconciliação de saldos contábeis.

Este comando deve ser executado diariamente (preferencialmente à noite)
para verificar a consistência dos saldos fixados em períodos fechados.

Uso:
    python manage.py verify_balances
    python manage.py verify_balances --period-id 123
    python manage.py verify_balances --send-email
    python manage.py verify_balances --fix
"""

from django.core.management.base import BaseCommand
from django.core.mail import mail_admins
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from treasury.models import AccountingPeriod
from treasury.services.period_service import PeriodService


class Command(BaseCommand):
    help = 'Verifica e reconcilia saldos contábeis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period-id',
            type=int,
            help='Verificar apenas um período específico',
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Enviar email para administradores se encontrar discrepâncias',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Tentar corrigir discrepâncias automaticamente (CUIDADO: uso experimental)',
        )

    def handle(self, *args, **options):
        """Executa a verificação de saldos."""
        period_id = options.get('period_id')
        send_email = options.get('send_email', False)
        fix = options.get('fix', False)

        self.stdout.write(self.style.SUCCESS('Iniciando verificação de saldos...'))
        self.stdout.write(f"Timestamp: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")

        # Buscar períodos para verificar
        if period_id:
            periods = AccountingPeriod.objects.filter(id=period_id)
            self.stdout.write(f"Verificando período ID: {period_id}")
        else:
            periods = AccountingPeriod.objects.filter(
                status__in=['closed', 'archived'],
                closing_balance__isnull=False
            )
            self.stdout.write(f"Verificando {periods.count()} períodos fechados/arquivados...")

        service = PeriodService()
        discrepancies = []

        for period in periods:
            self.stdout.write(f"\nVerificando {period.month_name}/{period.year}...", ending=' ')

            result = service.verify_period_balance(period)

            if result.get('is_consistent') is None:
                self.stdout.write(self.style.WARNING('PULADO'))
                self.stdout.write(f"  Motivo: {result.get('message', 'N/A')}")
                continue

            if result['is_consistent']:
                self.stdout.write(self.style.SUCCESS('OK'))
            else:
                self.stdout.write(self.style.ERROR('DISCREPÂNCIA'))
                discrepancies.append({
                    'period': period,
                    'result': result,
                })

                # Exibir detalhes da discrepância
                self.stdout.write(f"  Saldo fixado: {result['fixed_balance']}")
                self.stdout.write(f"  Saldo calculado: {result['calculated_balance']}")
                self.stdout.write(f"  Diferença: {result['difference']}")

                # Tentar corrigir se solicitado
                if fix:
                    self.fix_discrepancy(period, result)

        # Resumo
        self.stdout.write("\n" + "=" * 60)
        if discrepancies:
            self.stdout.write(
                self.style.ERROR(f"Encontradas {len(discrepancies)} discrepância(s)!")
            )

            if send_email:
                self.send_discrepancy_email(discrepancies)
                self.stdout.write("Email enviado para administradores.")
        else:
            self.stdout.write(self.style.SUCCESS("✓ Todos os saldos estão consistentes!"))

        # Verificar períodos abertos
        self.verify_open_periods()

    def fix_discrepancy(self, period, result):
        """
        Tenta corrigir uma discrepância automaticamente.

        ATENÇÃO: Esta é uma operação potencialmente perigosa.
        Use apenas se souber o que está fazendo.
        """
        self.stdout.write(self.style.WARNING(f"  Tentando corrigir período {period}..."))

        # Recalcular e atualizar
        period.closing_balance = result['calculated_balance']
        period.save(update_fields=['closing_balance'])

        # Adicionar nota
        original_notes = period.notes or ''
        period.notes = f"[CORREÇÃO AUTOMÁTICA EM {timezone.now().strftime('%d/%m/%Y %H:%M')}] {original_notes}"
        period.save(update_fields=['notes'])

        self.stdout.write(self.style.WARNING(f"  Saldo corrigido para: {result['calculated_balance']}"))

    def verify_open_periods(self):
        """Verifica se há períodos abertos que deveriam ser fechados."""
        self.stdout.write("\nVerificando períodos abertos...")

        open_periods = AccountingPeriod.objects.filter(status='open').order_by('-month')

        for period in open_periods:
            # Se o período é de mais de 2 meses atrás, alertar
            months_diff = (timezone.now().date().year - period.month.year) * 12 + \
                         (timezone.now().date().month - period.month.month)

            if months_diff > 2:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ATENÇÃO: {period.month_name}/{period.year} "
                        f"está aberto há {months_diff} meses. Considere fechar."
                    )
                )

    def send_discrepancy_email(self, discrepancies):
        """Envia email para administradores sobre discrepâncias."""
        subject = f"[{getattr(settings, 'SITE_NAME', 'Tesouraria')}] Discrepâncias em saldos contábeis"

        message = f"Foram encontradas {len(discrepancies)} discrepância(s) na verificação de saldos.\n\n"
        message += f"Timestamp: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        message += "=" * 60 + "\n\n"

        for item in discrepancies:
            period = item['period']
            result = item['result']

            message += f"Período: {period.month_name}/{period.year}\n"
            message += f"  Saldo fixado: R$ {result['fixed_balance']}\n"
            message += f"  Saldo calculado: R$ {result['calculated_balance']}\n"
            message += f"  Diferença: R$ {result['difference']}\n\n"

        message += "\nAcesse o sistema para mais detalhes e correções."

        mail_admins(subject, message, fail_silently=True)
