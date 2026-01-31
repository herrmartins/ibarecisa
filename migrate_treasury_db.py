#!/usr/bin/env python
"""
Script de migração do banco de dados do Treasury (schema antigo -> novo)

Uso:
    python migrate_treasury_db.py

AVISO: Sempre faça backup do banco antes de executar em produção!
"""

import os
import sys
import django
import shutil
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibarecisa.settings')
django.setup()

from django.db import connection
from django.conf import settings


def backup_database():
    """Cria um backup do banco de dados."""
    db_path = settings.DATABASES['default']['NAME']
    if not os.path.exists(db_path):
        print(f"⚠️  Banco de dados não encontrado: {db_path}")
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"

    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup criado: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return None


def execute_sql(cursor, sql, description=""):
    """Executa SQL e trata erros."""
    try:
        cursor.execute(sql)
        if description:
            row_count = cursor.rowcount if cursor.rowcount >= 0 else "OK"
            print(f"✅ {description} ({row_count} linhas afetadas)")
        return True
    except Exception as e:
        error_msg = str(e)
        if "duplicate column" in error_msg.lower() or "already exists" in error_msg.lower():
            if description:
                print(f"⏭️  {description} (já existe - pulando)")
            return True
        print(f"❌ Erro em '{description}': {e}")
        return False


def table_exists(cursor, table_name):
    """Verifica se a tabela existe."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        [table_name]
    )
    return cursor.fetchone() is not None


def column_exists(cursor, table_name, column_name):
    """Verifica se a coluna existe na tabela."""
    if not table_exists(cursor, table_name):
        return False
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_database():
    """Executa a migração do banco de dados."""

    print("\n" + "="*60)
    print("🔄 MIGRAÇÃO DO BANCO DE DADOS TREASURY")
    print("="*60 + "\n")

    # 1. Backup
    print("1️⃣  Criando backup do banco de dados...")
    backup_path = backup_database()
    if not backup_path:
        print("❌ Não foi possível criar backup. Abortando.")
        return False

    # 2. Conectar ao banco
    print("\n2️⃣  Conectando ao banco de dados...")
    db_path = settings.DATABASES['default']['NAME']
    print(f"   Banco: {db_path}")

    try:
        conn = connection.cursor()
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

    success = True
    steps_completed = 0

    # 3. Limpar foreign keys órfãs
    print("\n3️⃣  Limpando foreign keys órfãs...")

    execute_sql(
        conn,
        "DELETE FROM reversion_revision WHERE user_id NOT IN (SELECT id FROM users_customuser);",
        "   - reversion_revision limpo"
    )

    execute_sql(
        conn,
        "DELETE FROM users_customuser_groups WHERE customuser_id NOT IN (SELECT id FROM users_customuser);",
        "   - users_customuser_groups limpo"
    )

    execute_sql(
        conn,
        "DELETE FROM users_customuser_user_permissions WHERE customuser_id NOT IN (SELECT id FROM users_customuser);",
        "   - users_customuser_user_permissions limpo"
    )

    # 4. Criar tabela accountingperiod (se não existir)
    print("\n4️⃣  Criando tabela treasury_accountingperiod...")

    if not table_exists(conn, 'treasury_accountingperiod'):
        sql = """
        CREATE TABLE treasury_accountingperiod (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month DATE NOT NULL UNIQUE,
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            opening_balance DECIMAL(10,2) NOT NULL DEFAULT 0.0,
            closing_balance DECIMAL(10,2) NULL,
            closed_at TIMESTAMP NULL,
            closed_by_id INTEGER NULL,
            notes TEXT NULL,
            created_at TIMESTAMP NULL,
            updated_at TIMESTAMP NULL,
            FOREIGN KEY (closed_by_id) REFERENCES users_customuser(id)
        );
        """
        if execute_sql(conn, sql, "   - tabela criada"):
            steps_completed += 1
    else:
        print("   - tabela já existe (pulando)")
        steps_completed += 1

    # 5. Migrar dados de monthlybalance para accountingperiod
    print("\n5️⃣  Migrando dados de monthlybalance para accountingperiod...")

    if table_exists(conn, 'treasury_monthlybalance'):
        sql = """
        INSERT OR IGNORE INTO treasury_accountingperiod
            (id, month, status, opening_balance, closing_balance, created_at, updated_at)
        SELECT
            id,
            month,
            CASE WHEN balance > 0 THEN 'closed' ELSE 'open' END as status,
            0.0 as opening_balance,
            balance as closing_balance,
            created as created_at,
            modified as updated_at
        FROM treasury_monthlybalance;
        """
        if execute_sql(conn, sql, "   - dados migrados"):
            steps_completed += 1
    else:
        print("   - treasury_monthlybalance não existe (pulando)")
        steps_completed += 1

    # 6. Adicionar colunas faltando em transactionmodel
    print("\n6️⃣  Adicionando colunas faltando em transactionmodel...")

    columns_to_add = [
        ("transaction_type", "VARCHAR(20) DEFAULT 'original'"),
        ("created_at", "TIMESTAMP"),
        ("updated_at", "TIMESTAMP"),
        ("accounting_period_id", "INTEGER NULL"),
        ("reverses_id", "INTEGER NULL"),
        ("created_by_id", "INTEGER NULL"),
    ]

    for col_name, col_type in columns_to_add:
        if not column_exists(conn, 'treasury_transactionmodel', col_name):
            sql = f"ALTER TABLE treasury_transactionmodel ADD COLUMN {col_name} {col_type};"
            if execute_sql(conn, sql, f"   - {col_name} adicionada"):
                steps_completed += 1
        else:
            print(f"   - {col_name} já existe (pulando)")
            steps_completed += 1

    # 7. Vincular transações aos períodos contábeis
    print("\n7️⃣  Vinculando transações aos períodos contábeis...")

    if column_exists(conn, 'treasury_transactionmodel', 'accounting_period_id'):
        sql = """
        UPDATE treasury_transactionmodel
        SET accounting_period_id = (
            SELECT id FROM treasury_accountingperiod
            WHERE strftime('%Y-%m', treasury_transactionmodel.date) = strftime('%Y-%m', month)
            LIMIT 1
        )
        WHERE accounting_period_id IS NULL;
        """
        if execute_sql(conn, sql, "   - transações vinculadas"):
            steps_completed += 1
    else:
        print("   - coluna accounting_period_id não existe (pulando)")

    # 8. Preencher created_by_id
    print("\n8️⃣  Preenchendo created_by_id...")

    if column_exists(conn, 'treasury_transactionmodel', 'created_by_id'):
        sql = """
        UPDATE treasury_transactionmodel
        SET created_by_id = user_id
        WHERE created_by_id IS NULL;
        """
        if execute_sql(conn, sql, "   - created_by_id preenchido"):
            steps_completed += 1
    else:
        print("   - coluna created_by_id não existe (pulando)")

    # Commit das alterações
    conn.execute("COMMIT")

    # 9. Estatísticas finais
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS FINAIS")
    print("="*60)

    try:
        from treasury.models import TransactionModel, AccountingPeriod

        print(f"\n   Transações totais: {TransactionModel.objects.count()}")
        print(f"   Transações originais: {TransactionModel.objects.filter(transaction_type='original').count()}")
        print(f"   Estornos: {TransactionModel.objects.filter(transaction_type='reversal').count()}")
        print(f"   Períodos contábeis: {AccountingPeriod.objects.count()}")

        # Mostrar alguns períodos
        print("\n   Períodos recentes:")
        for p in AccountingPeriod.objects.all().order_by('-month')[:5]:
            print(f"      - {p.month_name}/{p.year}: {p.status}, saldo={p.closing_balance or 'N/A'}")

    except Exception as e:
        print(f"\n   ⚠️  Erro ao obter estatísticas: {e}")

    print("\n" + "="*60)
    print(f"✅ Migração concluída! {steps_completed} etapas concluídas.")
    print(f"📁 Backup salvo em: {backup_path}")
    print("="*60 + "\n")

    print("🔔 Próximo passo: execute 'python manage.py migrate --fake' para marcar as migrações como aplicadas.\n")

    return True


def main():
    """Função principal."""
    try:
        success = migrate_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migração interrompida pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
