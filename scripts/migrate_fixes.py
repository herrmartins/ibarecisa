#!/usr/bin/env python
"""
Script de correções para migrar dados de produção para desenvolvimento.

Rodar após importar o banco de produção:
    python manage.py shell < migrate_fixes.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibarecisa.settings')
django.setup()

from treasury.models import AccountingPeriod
from django.db.models import Sum
from django.db.models.functions import Coalesce
from decimal import Decimal


def recalc_opening_balances():
    """
    Recalcula todos os opening_balance em ordem cronológica.
    Isso garante que cada período herde corretamente o saldo do anterior.
    """
    print("=== Recalculando opening_balance de todos os períodos ===\n")

    periods = AccountingPeriod.objects.all().order_by('month')
    running_balance = Decimal('0.00')

    for period in periods:
        old_opening = period.opening_balance

        # Calcular o net das transações
        transactions = period.transactions.filter(transaction_type='original')
        net = transactions.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total'] or Decimal('0.00')

        # Atualizar opening_balance
        period.opening_balance = running_balance
        period.save(update_fields=['opening_balance'])

        # Atualizar running_balance para o próximo período
        running_balance += net

        # Se período está fechado, atualizar também closing_balance
        if period.is_closed:
            period.closing_balance = running_balance
            period.save(update_fields=['closing_balance'])

        print(f'{period.month.strftime("%m/%Y")}: opening {old_opening:.2f} -> {period.opening_balance:.2f}, closing {period.closing_balance}')

    print(f'\nSaldo final acumulado: R$ {running_balance:.2f}\n')


def recalc_closing_balances():
    """
    Recalcula apenas os closing_balance dos períodos fechados.
    Usa a fórmula: opening_balance + sum(amount) de todas as transações.
    """
    print("=== Recalculando closing_balance de períodos fechados ===\n")

    periods = AccountingPeriod.objects.filter(status='closed').order_by('month')

    for period in periods:
        old_closing = period.closing_balance

        # Calcular net das transações (transações negativas já têm amount negativo)
        transactions = period.transactions.filter(transaction_type='original')
        net = transactions.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total'] or Decimal('0.00')

        # Novo closing_balance
        new_closing = period.opening_balance + net
        period.closing_balance = new_closing
        period.save(update_fields=['closing_balance'])

        print(f'{period.month.strftime("%m/%Y")}: {old_closing:.2f} -> {new_closing:.2f}')

    print()


def delete_future_periods():
    """
    Deleta períodos futuros (sem transações) que possam ter sido criados.
    """
    from django.utils import timezone

    print("=== Verificando períodos futuros ===\n")

    today = timezone.now().date()
    current_month = today.replace(day=1)

    future_periods = AccountingPeriod.objects.filter(month__gt=current_month)

    for period in future_periods:
        tx_count = period.transactions.count()
        print(f'{period.month.strftime("%m/%Y")}: {tx_count} transações')

        if tx_count == 0:
            print(f'  -> Deletando (sem transações)')
            period.delete()
        else:
            print(f'  -> Mantendo (tem transações)')

    print()


def verify_all_periods():
    """
    Verifica a consistência de todos os períodos.
    """
    print("=== Verificando consistência dos períodos ===\n")

    periods = AccountingPeriod.objects.all().order_by('month')

    has_issues = False

    for period in periods:
        # Calcular o valor esperado
        transactions = period.transactions.filter(transaction_type='original')
        net = transactions.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total'] or Decimal('0.00')

        expected_closing = period.opening_balance + net

        if period.is_closed:
            if period.closing_balance != expected_closing:
                has_issues = True
                print(f'❌ {period.month.strftime("%m/%Y")}: closing incorreto!')
                print(f'   Esperado: {expected_closing:.2f}, Atual: {period.closing_balance:.2f}')
            else:
                print(f'✓ {period.month.strftime("%m/%Y")}: OK')
        else:
            current_calc = period.opening_balance + net
            print(f'○ {period.month.strftime("%m/%Y")}: aberto (calculado: {current_calc:.2f})')

    if not has_issues:
        print('\n✓ Todos os períodos fechados estão consistentes!')
    else:
        print('\n⚠ Foram encontradas inconsistências. Rode recalc_closing_balances()')

    print()


def main():
    """Executa todas as correções."""
    print("=" * 60)
    print("MIGRAÇÃO E CORREÇÕES - TESOURARIA")
    print("=" * 60)
    print()

    # Passo 1: Deletar períodos futuros sem transações
    delete_future_periods()

    # Passo 2: Recalcular opening_balance (garante a cadeia)
    recalc_opening_balances()

    # Passo 3: Recalcular closing_balance dos períodos fechados
    recalc_closing_balances()

    # Passo 4: Verificar consistência
    verify_all_periods()

    print("=" * 60)
    print("CONCLUÍDO!")
    print("=" * 60)


if __name__ == '__main__':
    main()
else:
    # Se for importado via shell, roda automaticamente
    main()
