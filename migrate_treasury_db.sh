#!/bin/bash
#
# Script de migração do banco de dados Treasury (schema antigo -> novo)
#
# Uso:
#     ./migrate_treasury_db.sh
#
# AVISO: Sempre faça backup do banco antes de executar em produção!

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "============================================"
echo "🔄 MIGRAÇÃO DO BANCO DE DADOS TREASURY"
echo "============================================"
echo ""

# Verificar se o banco existe
DB_FILE="db.sqlite3"
if [ ! -f "$DB_FILE" ]; then
    echo -e "${RED}❌ Banco de dados não encontrado: $DB_FILE${NC}"
    exit 1
fi

# 1. Backup
echo "1️⃣  Criando backup do banco de dados..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${DB_FILE}.backup_${TIMESTAMP}"
cp "$DB_FILE" "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup criado: $BACKUP_FILE${NC}"
echo ""

# Função para executar SQL com tratamento de erro
exec_sql() {
    DESCRIPTION=$1
    SQL=$2

    sqlite3 "$DB_FILE" "$SQL" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $DESCRIPTION${NC}"
    else
        echo -e "${YELLOW}⚠️  $DESCRIPTION (pode já existir)${NC}"
    fi
}

# 2. Limpar foreign keys órfãs
echo "2️⃣  Limpando foreign keys órfãs..."
exec_sql "   - reversion_revision limpo" \
    "DELETE FROM reversion_revision WHERE user_id NOT IN (SELECT id FROM users_customuser);"
exec_sql "   - reversion_version limpo" \
    "DELETE FROM reversion_version WHERE revision_id NOT IN (SELECT id FROM reversion_revision);"
exec_sql "   - users_customuser_groups limpo" \
    "DELETE FROM users_customuser_groups WHERE customuser_id NOT IN (SELECT id FROM users_customuser);"
exec_sql "   - users_customuser_user_permissions limpo" \
    "DELETE FROM users_customuser_user_permissions WHERE customuser_id NOT IN (SELECT id FROM users_customuser);"
echo ""

# 3. Criar tabela accountingperiod
echo "3️⃣  Criando tabela treasury_accountingperiod..."
exec_sql "   - tabela criada" \
    "CREATE TABLE IF NOT EXISTS treasury_accountingperiod (
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
    );"

# Criar tabela reversaltransaction
exec_sql "   - tabela reversaltransaction criada" \
    "CREATE TABLE IF NOT EXISTS treasury_reversaltransaction (
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
    );"
echo ""

# 4. Migrar dados de monthlybalance
echo "4️⃣  Migrando dados de monthlybalance..."
exec_sql "   - dados migrados" \
    "INSERT OR IGNORE INTO treasury_accountingperiod
        (id, month, status, opening_balance, closing_balance, created_at, updated_at)
    SELECT
        id,
        month,
        CASE WHEN balance > 0 THEN 'closed' ELSE 'open' END as status,
        0.0 as opening_balance,
        balance as closing_balance,
        created as created_at,
        modified as updated_at
    FROM treasury_monthlybalance;"
echo ""

# 5. Adicionar colunas faltando em transactionmodel
echo "5️⃣  Adicionando colunas em transactionmodel..."
exec_sql "   - transaction_type" \
    "ALTER TABLE treasury_transactionmodel ADD COLUMN transaction_type VARCHAR(20) DEFAULT 'original';"
exec_sql "   - created_at" \
    "ALTER TABLE treasury_transactionmodel ADD COLUMN created_at TIMESTAMP;"
exec_sql "   - updated_at" \
    "ALTER TABLE treasury_transactionmodel ADD COLUMN updated_at TIMESTAMP;"
exec_sql "   - accounting_period_id" \
    "ALTER TABLE treasury_transactionmodel ADD COLUMN accounting_period_id INTEGER NULL;"
exec_sql "   - reverses_id" \
    "ALTER TABLE treasury_transactionmodel ADD COLUMN reverses_id INTEGER NULL;"
exec_sql "   - created_by_id" \
    "ALTER TABLE treasury_transactionmodel ADD COLUMN created_by_id INTEGER NULL;"
echo ""

# 6. Vincular transações aos períodos
echo "6️⃣  Vinculando transações aos períodos..."
exec_sql "   - transações vinculadas" \
    "UPDATE treasury_transactionmodel
    SET accounting_period_id = (
        SELECT id FROM treasury_accountingperiod
        WHERE strftime('%Y-%m', treasury_transactionmodel.date) = strftime('%Y-%m', month)
        LIMIT 1
    )
    WHERE accounting_period_id IS NULL;"
echo ""

# 7. Preencher created_by_id
echo "7️⃣  Preenchendo created_by_id..."
exec_sql "   - created_by_id preenchido" \
    "UPDATE treasury_transactionmodel
    SET created_by_id = user_id
    WHERE created_by_id IS NULL;"
echo ""

# 8. Estatísticas
echo "============================================"
echo "📊 ESTATÍSTICAS"
echo "============================================"
echo ""

echo -e "${BLUE}Transações:${NC}"
sqlite3 "$DB_FILE" "SELECT '   Total: ' || COUNT(*) FROM treasury_transactionmodel;"
sqlite3 "$DB_FILE" "SELECT '   Originais: ' || COUNT(*) FROM treasury_transactionmodel WHERE transaction_type = 'original';"
sqlite3 "$DB_FILE" "SELECT '   Estornos: ' || COUNT(*) FROM treasury_transactionmodel WHERE transaction_type = 'reversal';"

echo ""
echo -e "${BLUE}Períodos:${NC}"
sqlite3 "$DB_FILE" "SELECT '   Total: ' || COUNT(*) FROM treasury_accountingperiod;"

echo ""
echo -e "${BLUE}Estornos:${NC}"
sqlite3 "$DB_FILE" "SELECT '   Total: ' || COUNT(*) FROM treasury_reversaltransaction;"

echo ""
echo "============================================"
echo -e "${GREEN}✅ Migração concluída!${NC}"
echo "📁 Backup: $BACKUP_FILE"
echo "============================================"
echo ""
echo -e "${YELLOW}🔔 Próximo: python manage.py migrate --fake${NC}"
echo ""
