# Deploy para Produção - Nova Sistemática de Permissões

## 📋 Data Migration Automática

A migration `0015_migrate_monthly_balance_to_accounting_period` foi criada para converter
automaticamente o schema antigo para o novo. Ela é **IDEMPOTENTE** - pode ser rodada
múltiplas vezes sem problemas.

## 🚀 Procedimento de Deploy

### Passo 1: Backup do Banco (Opcional mas Recomendado)

```bash
# No servidor de produção
cd /caminho/do/projeto
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
cp audit.sqlite3 audit.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
```

### Passo 2: Atualizar Código

```bash
git pull origin dev
# OU se estiver usando main:
git pull origin main
```

### Passo 3: Instalar Dependências (se necessário)

```bash
pip install -r requirements.txt
# OU usando uv:
uv sync
```

### Passo 4: Rodar Migrations

```bash
# Migrar banco principal
python manage.py migrate

# Migrar banco de auditoria (se estiver vazio ou não existir)
python manage.py migrate --database=audit
```

**Isso é tudo!** A migration 0015 detectará automaticamente se o schema antigo existe
e fará a conversão necessária.

### Passo 5: Verificar Funcionamento

```bash
python manage.py check
python manage.py test treasury.tests.test_permissions
```

## ✅ O que a Migration Faz

A migration `0015` executa automaticamente:

1. **Detecta** se a tabela `treasury_monthlybalance` existe
2. **Cria** a tabela `treasury_accountingperiod` (se não existir)
3. **Migra** os dados de `monthlybalance` para `accountingperiod`
4. **Adiciona** colunas na `treasury_transactionmodel`:
   - `transaction_type`
   - `created_at`
   - `updated_at`
   - `accounting_period_id`
   - `reverses_id`
   - `created_by_id`
5. **Vincula** as transações aos períodos contábeis
6. **Preenche** o campo `created_by_id`

## 🔐 Novas Permissões Implementadas

### Usuários Comuns (Membros)
- ✅ Visualizar dashboard, listas, gráficos, relatórios
- ❌ Criar, editar, excluir transações
- ❌ Acessar formulários de criação/edição
- ❌ Gerar insights IA, usar OCR, fechar períodos

### Tesoureiros/Secretários/Pastores/Staff
- ✅ Acesso total a todas as funcionalidades

## 📊 Estrutura de Arquivos

```
treasury/
├── migrations/
│   └── 0015_migrate_monthly_balance_to_accounting_period.py  # ← Nova migration
├── mixins.py                                                  # ← IsTreasuryUserMixin
├── views/
│   └── template_views.py                                      # ← Views com permissões
└── api/
    └── views.py                                               # ← API com permissões
```

## 🧪 Testes Locais

Antes de fazer deploy em produção, você pode testar localmente:

```bash
# Copiar banco de produção para teste
cp db.sqlite3 db.sqlite3.test

# Rodar migrations
python manage.py migrate

# Rodar testes
python manage.py test treasury.tests.test_permissions

# Verificar dados
sqlite3 db.sqlite3 "SELECT COUNT(*) FROM treasury_accountingperiod;"
sqlite3 db.sqlite3 "SELECT COUNT(*) FROM treasury_transactionmodel;"
```

## 📞 Suporte

Em caso de problemas:
1. Verificar logs: `python manage.py check`
2. Reverter para o backup
3. Rodar migrations novamente (são idempotentes)
