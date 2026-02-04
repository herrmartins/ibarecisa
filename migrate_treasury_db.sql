-- ============================================
-- MIGRAÇÃO DO BANCO DE DADOS TREASURY
-- Schema antigo -> novo
--
-- Uso: sqlite3 db.sqlite3 < migrate_treasury_db.sql
--
-- AVISO: Faça backup antes de executar!
-- ============================================

-- ============================================
-- 1. LIMPAR FOREIGN KEYS ÓRFÃS
-- ============================================
DELETE FROM reversion_revision WHERE user_id NOT IN (SELECT id FROM users_customuser);
DELETE FROM users_customuser_groups WHERE customuser_id NOT IN (SELECT id FROM users_customuser);
DELETE FROM users_customuser_user_permissions WHERE customuser_id NOT IN (SELECT id FROM users_customuser);

-- ============================================
-- 2. CRIAR TABELA treasury_accountingperiod
-- (se não existir)
-- ============================================
CREATE TABLE IF NOT EXISTS treasury_accountingperiod (
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

-- ============================================
-- 3. MIGRAR DADOS DE monthlybalance PARA accountingperiod
-- ============================================
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

-- ============================================
-- 4. ADICIONAR COLUNAS EM transactionmodel
-- (se não existirem)
-- ============================================

-- transaction_type
-- SQLite não suporta ADD COLUMN IF NOT EXISTS diretamente,
-- então usamos uma abordagem diferente
-- Se der erro de coluna duplicada, ignore e continue

-- Tentar adicionar cada coluna (ignorar erros de duplicata)
ALTER TABLE treasury_transactionmodel ADD COLUMN transaction_type VARCHAR(20) DEFAULT 'original';

ALTER TABLE treasury_transactionmodel ADD COLUMN created_at TIMESTAMP;

ALTER TABLE treasury_transactionmodel ADD COLUMN updated_at TIMESTAMP;

ALTER TABLE treasury_transactionmodel ADD COLUMN accounting_period_id INTEGER NULL;

ALTER TABLE treasury_transactionmodel ADD COLUMN reverses_id INTEGER NULL;

ALTER TABLE treasury_transactionmodel ADD COLUMN created_by_id INTEGER NULL;

-- ============================================
-- 5. VINCULAR TRANSAÇÕES AOS PERÍODOS CONTÁBEIS
-- ============================================
UPDATE treasury_transactionmodel
SET accounting_period_id = (
    SELECT id FROM treasury_accountingperiod
    WHERE strftime('%Y-%m', treasury_transactionmodel.date) = strftime('%Y-%m', month)
    LIMIT 1
)
WHERE accounting_period_id IS NULL;

-- ============================================
-- 6. PREENCHER created_by_id
-- ============================================
UPDATE treasury_transactionmodel
SET created_by_id = user_id
WHERE created_by_id IS NULL;

-- ============================================
-- MIGRAÇÃO CONCLUÍDA
-- ============================================

-- Para verificar os resultados, execute:
-- SELECT 'Transações:', COUNT(*) FROM treasury_transactionmodel;
-- SELECT 'Períodos:', COUNT(*) FROM treasury_accountingperiod;
