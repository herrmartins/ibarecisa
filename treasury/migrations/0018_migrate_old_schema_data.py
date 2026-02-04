# Generated manually - Migration para migrar dados do schema antigo
"""
Migration para migrar os DADOS do schema antigo (treasury_monthlybalance)
para o novo schema (treasury_accountingperiod).

Esta migration assume que as tabelas já existem (foram criadas pelas migrations
anteriores como 0002), e só precisa migrar os dados.

Use após a 0017 (ou 0016 se não usar merge).
"""

from django.db import migrations, connection


def migrate_old_schema_data(apps, schema_editor):
    """
    Migra os dados do schema antigo para o novo.
    Assume que as tabelas já existem.
    """
    cursor = connection.cursor()

    # 1. Verificar se a tabela antiga existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='treasury_monthlybalance';
    """)
    old_table_exists = cursor.fetchone() is not None

    if not old_table_exists:
        print("Schema antigo não encontrado - nada a migrar.")
        return

    # 2. Verificar se JÁ há dados migrados
    cursor.execute("SELECT COUNT(*) FROM treasury_accountingperiod;")
    existing_periods = cursor.fetchone()[0]

    if existing_periods > 0:
        print(f"Já existem {existing_periods} períodos - verificando se precisa migrar...")
        # Se já tem períodos e transações vinculadas, não faz nada
        cursor.execute("""
            SELECT COUNT(*) FROM treasury_transactionmodel
            WHERE accounting_period_id IS NOT NULL;
        """)
        linked = cursor.fetchone()[0]
        if linked > 0:
            print(f"Já existem {linked} transações vinculadas - migração já foi feita.")
            return
        print("Períodos existem mas não há transações vinculadas - continuando...")

    print("Migrando dados do schema antigo...")

    # 3. Se não há períodos, criar a partir de monthlybalance
    if existing_periods == 0:
        print("Criando períodos a partir de monthlybalance...")
        cursor.execute("""
            INSERT INTO treasury_accountingperiod
                (month, status, opening_balance, closing_balance, created_at, updated_at, notes, is_first_month)
            SELECT
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
        print(f"Criados {cursor.rowcount} períodos.")
    else:
        print(f"Já existem {existing_periods} períodos - pulando criação.")

    # 4. Adicionar coluna accounting_period_id se não existir
    cursor.execute("PRAGMA table_info(treasury_transactionmodel);")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if 'accounting_period_id' not in existing_columns:
        print("Adicionando coluna accounting_period_id...")
        cursor.execute("""
            ALTER TABLE treasury_transactionmodel
            ADD COLUMN accounting_period_id INTEGER NULL;
        """)
        # Criar a foreign key constraint (SQLite não suporta ADD CONSTRAINT com ALTER TABLE,
        # mas o Django vai validar no nível de aplicação)

    # 5. Vincular transações aos períodos
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
    print(f"Vinculadas {cursor.rowcount} transações.")

    # 6. Verificar resultado
    cursor.execute("SELECT COUNT(*) FROM treasury_accountingperiod;")
    total_periods = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM treasury_transactionmodel
        WHERE accounting_period_id IS NOT NULL;
    """)
    linked_transactions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM treasury_transactionmodel;")
    total_transactions = cursor.fetchone()[0]

    print(f"\n=== Migração concluída ===")
    print(f"Períodos criados: {total_periods}")
    print(f"Transações vinculadas: {linked_transactions} de {total_transactions}")
    print(f"Transações sem vínculo: {total_transactions - linked_transactions}")


def reverse_migration(apps, schema_editor):
    """Não é possível reverter facilmente esta migration."""
    print("AVISO: Esta migration não pode ser revertida automaticamente.")
    print("Se precisar reverter, você precisará:")
    print("1. Salvar os dados migrados")
    print("2. Deletar os períodos e transações")
    print("3. Recriar o schema antigo")


class Migration(migrations.Migration):

    dependencies = [
        ('treasury', '0017_merge_schema_migrations'),
    ]

    operations = [
        migrations.RunPython(migrate_old_schema_data, reverse_migration),
    ]
