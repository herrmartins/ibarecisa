#!/bin/bash
#
# Script completo de migração de produção para desenvolvimento
#
# Uso:
#   1. Copiar db.sqlite3 de produção para este diretório
#   2. ./migrate_production.sh
#

set -e  # Para em caso de erro

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

DB_FILE="db.sqlite3"

echo ""
echo "============================================"
echo "🔄 MIGRAÇÃO PRODUÇÃO -> DEV"
echo "============================================"
echo ""

# 1. Backup
echo "1️⃣  Criando backup..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp "$DB_FILE" "${DB_FILE}.backup_${TIMESTAMP}"
echo -e "${GREEN}✅ Backup criado${NC}"
echo ""

# 2. Verificar se precisa rodar migrate_treasury_db.sh
echo "2️⃣  Verificando schema..."

# Verifica se a tabela treasury_accountingperiod existe
TABLE_EXISTS=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='treasury_accountingperiod';" 2>/dev/null)

if [ -z "$TABLE_EXISTS" ]; then
    echo -e "${YELLOW}⚠️  Schema antigo detectado (treasury_monthlybalance)${NC}"
    echo "   Rodando migrate_treasury_db.sh..."
    ./migrate_treasury_db.sh
    echo -e "${GREEN}✅ Schema migrado${NC}"
else
    echo -e "${GREEN}✅ Schema novo já presente (treasury_accountingperiod)${NC}"
fi
echo ""

# 3. Verificar se a tabela django_migrations existe
echo "3️⃣  Verificando migrations do Django..."

MIGRATIONS_TABLE=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='django_migrations';" 2>/dev/null)

if [ -z "$MIGRATIONS_TABLE" ]; then
    echo -e "${YELLOW}⚠️  Tabela django_migrations não existe${NC}"
    echo "   Criando tabela..."
    sqlite3 "$DB_FILE" "CREATE TABLE django_migrations (id INTEGER PRIMARY KEY AUTOINCREMENT, app VARCHAR(255) NOT NULL, name VARCHAR(255) NOT NULL, applied TIMESTAMP NOT NULL);"
    echo -e "${GREEN}✅ Tabela criada${NC}"
else
    echo -e "${GREEN}✅ Tabela django_migrations existe${NC}"
fi
echo ""

# 4. Marcar migrations do treasury como aplicadas (se já rodou o script)
echo "4️⃣  Sincronizando migrations do Treasury..."

# Verificar quais migrations do treasury já estão aplicadas
APPLIED_MIGRATIONS=$(sqlite3 "$DB_FILE" "SELECT name FROM django_migrations WHERE app='treasury' ORDER BY name;" 2>/dev/null)

# Lista de migrations do treasury em ordem
MIGRATION_LIST=(
    "0001_initial"
    "0002_transactionmodel_created_at_and_more"
    "0003_periodsnapshot_auditlog"
    "0004_remove_auditlog_audit_log_user_id_79f582_idx_and_more"
)

for migration in "${MIGRATION_LIST[@]}"; do
    ALREADY_APPLIED=$(echo "$APPLIED_MIGRATIONS" | grep -c "^${migration}$" || true)
    if [ "$ALREADY_APPLIED" -eq 0 ]; then
        echo "   Marcando $migration como aplicada..."
        sqlite3 "$DB_FILE" "INSERT INTO django_migrations (app, name, applied) VALUES ('treasury', '$migration', datetime('now'));"
    fi
done

echo -e "${GREEN}✅ Migrations sincronizadas${NC}"
echo ""

# 5. Rodar migrate do Django (só vai rodar migrations que faltam)
echo "5️⃣  Rodando migrate do Django..."

# Detectar e usar o Python do venv
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
else
    PYTHON="python3"
fi

$PYTHON manage.py migrate --fake-initial
echo -e "${GREEN}✅ Migrate concluído${NC}"
echo ""

# 6. Rodar script de correções dos saldos
echo "6️⃣  Corrigindo saldos..."
$PYTHON manage.py shell < scripts/migrate_fixes.py
echo ""

echo "============================================"
echo -e "${GREEN}✅ MIGRAÇÃO CONCLUÍDA!${NC}"
echo "============================================"
echo ""
echo -e "${BLUE}📁 Backup: ${DB_FILE}.backup_${TIMESTAMP}${NC}"
echo ""
echo -e "${YELLOW}Próximo: iniciar o servidor${NC}"
echo "  python3 manage.py runserver"
echo ""
