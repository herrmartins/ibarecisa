# Generated manually - Migration para converter schema antigo antes das migrations normais
"""
Migration para converter o schema antigo (treasury_monthlybalance)
para o novo schema (treasury_accountingperiod) ANTES das migrations
normais do Django.

Esta migration DEVE rodar antes da 0002 que tenta criar a tabela
accountingperiod.

Execute: python manage.py migrate treasury 0001_5 --fake-initial
"""

from django.db import migrations, connection


def convert_old_schema(apps, schema_editor):
    """
    Converte o schema antigo para o novo.

    Esta função detecta se o schema antigo existe e faz a conversão
    necessária antes que as migrations normais tentem criar as tabelas.
    """
    cursor = connection.cursor()

    # 0. Limpar foreign keys órfãs (comum em bancos de produção antigos)
    print("Limpando foreign keys órfãs...")
    cursor.execute("DELETE FROM reversion_revision WHERE user_id NOT IN (SELECT id FROM users_customuser);")
    cursor.execute("DELETE FROM reversion_version WHERE revision_id NOT IN (SELECT id FROM reversion_revision);")
    cursor.execute("DELETE FROM users_customuser_groups WHERE customuser_id NOT IN (SELECT id FROM users_customuser);")
    cursor.execute("DELETE FROM users_customuser_user_permissions WHERE customuser_id NOT IN (SELECT id FROM users_customuser);")

    # 1. Verificar se a tabela antiga existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='treasury_monthlybalance';
    """)
    old_table_exists = cursor.fetchone() is not None

    if not old_table_exists:
        # Schema antigo não existe - nada a fazer
        return

    # 2. Verificar se a tabela nova já existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='treasury_accountingperiod';
    """)
    new_table_exists = cursor.fetchone() is not None

    if new_table_exists:
        # Tabela nova já existe - migration já rodou ou script já rodou
        return

    print("Detectado schema antigo - convertendo para novo schema...")

    # 3. Criar tabela treasury_accountingperiod
    cursor.execute("""
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
            is_first_month BOOLEAN DEFAULT 0,
            FOREIGN KEY (closed_by_id) REFERENCES users_customuser(id)
        );
    """)

    # 4. Migrar dados de monthlybalance para accountingperiod
    cursor.execute("""
        INSERT INTO treasury_accountingperiod
            (id, month, status, opening_balance, closing_balance, created_at, updated_at, notes, is_first_month)
        SELECT
            id,
            month,
            CASE WHEN balance > 0 THEN 'closed' ELSE 'open' END as status,
            0.0 as opening_balance,
            balance as closing_balance,
            created as created_at,
            modified as updated_at,
            '' as notes,
            0 as is_first_month
        FROM treasury_monthlybalance;
    """)

    # 5. Adicionar colunas na transactionmodel se não existirem
    cursor.execute("PRAGMA table_info(treasury_transactionmodel);")
    existing_columns = {row[1] for row in cursor.fetchall()}

    columns_to_add = {
        'transaction_type': "VARCHAR(20) DEFAULT 'original'",
        'created_at': 'TIMESTAMP',
        'updated_at': 'TIMESTAMP',
        'accounting_period_id': 'INTEGER NULL',
        'reverses_id': 'INTEGER NULL',
        'created_by_id': 'INTEGER NULL',
    }

    for column, definition in columns_to_add.items():
        if column not in existing_columns:
            print(f"Adicionando coluna {column}...")
            cursor.execute(f"""
                ALTER TABLE treasury_transactionmodel
                ADD COLUMN {column} {definition};
            """)

    # 6. Criar tabela treasury_reversaltransaction
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treasury_reversaltransaction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_transaction_id INTEGER NOT NULL,
            reversal_transaction_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            authorized_by_id INTEGER NULL,
            created_at TIMESTAMP NULL,
            created_by_id INTEGER NULL,
            FOREIGN KEY (original_transaction_id) REFERENCES treasury_transactionmodel(id),
            FOREIGN KEY (reversal_transaction_id) REFERENCES treasury_transactionmodel(id),
            FOREIGN KEY (authorized_by_id) REFERENCES users_customuser(id),
            FOREIGN KEY (created_by_id) REFERENCES users_customuser(id)
        );
    """)

    # 7. Vincular transações aos períodos
    print("Vinculando transações aos períodos...")
    cursor.execute("""
        UPDATE treasury_transactionmodel
        SET accounting_period_id = (
            SELECT id FROM treasury_accountingperiod
            WHERE strftime('%Y-%m', treasury_transactionmodel.date) = strftime('%Y-%m', month)
            LIMIT 1
        )
        WHERE accounting_period_id IS NULL;
    """)

    # 8. Preencher created_by_id
    print("Preenchendo created_by_id...")
    cursor.execute("""
        UPDATE treasury_transactionmodel
        SET created_by_id = user_id
        WHERE created_by_id IS NULL;
    """)

    print("Conversão do schema concluída!")


class Migration(migrations.Migration):

    dependencies = [
        ('treasury', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(convert_old_schema, migrations.RunPython.noop),
    ]
