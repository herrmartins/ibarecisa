/**
 * Alpine.js Components para o módulo de Tesouraria
 *
 * Componentes reutilizáveis para:
 * - Tabelas de transações
 * - Formulários de transação
 * - Modais de fechamento de período
 * - Cards de período
 * - Filtros
 */

// ============================================
// Tabela de Transações
// ============================================
Alpine.data('transactionTable', () => ({
    transactions: [],
    loading: false,
    filters: {
        period: null,
        category: null,
        search: '',
    },
    pagination: {
        page: 1,
        totalPages: 1,
    },

    init() {
        this.load();
    },

    async load(page = 1) {
        this.loading = true;
        try {
            const params = new URLSearchParams();
            if (this.filters.period) params.append('accounting_period', this.filters.period);
            if (this.filters.category) params.append('category', this.filters.category);
            if (this.filters.search) params.append('search', this.filters.search);
            params.append('page', page);

            const response = await fetch(`/treasury/api/transactions/?${params}`, {
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });

            const data = await response.json();
            this.transactions = data.results || data;
            this.pagination = {
                page: page,
                totalPages: Math.ceil((data.count || 0) / 50),
            };
        } finally {
            this.loading = false;
        }
    },

    async delete(id) {
        if (!confirm('Tem certeza que deseja excluir esta transação?')) return;

        try {
            const response = await fetch(`/treasury/api/transactions/${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });

            if (response.ok) {
                this.$store.ui.notify('Transação excluída com sucesso!', 'success');
                this.load();
            }
        } catch (err) {
            this.$store.ui.notify('Erro ao excluir transação', 'error');
        }
    },

    formatAmount(amount, isPositive) {
        const value = isPositive ? amount : -amount;
        return formatBRL(value);
    },

    amountClass(isPositive) {
        return isPositive ? 'text-green-600' : 'text-red-600';
    },
}));

// ============================================
// Formulário de Transação
// ============================================
Alpine.data('transactionForm', () => ({
    data: {
        description: '',
        amount: '',
        is_positive: true,
        date: new Date().toISOString().split('T')[0],
        category: '',
        acquittance_doc: null,
    },
    errors: {},
    submitting: false,

    get categories() {
        return this.$store.categories.categories || [];
    },

    init() {
        this.$store.categories.load();
    },

    validate() {
        this.errors = {};

        if (!this.data.description.trim()) {
            this.errors.description = 'A descrição é obrigatória.';
        }
        if (!this.data.amount || parseFloat(this.data.amount) <= 0) {
            this.errors.amount = 'O valor deve ser positivo.';
        }
        if (!this.data.date) {
            this.errors.date = 'A data é obrigatória.';
        }

        return Object.keys(this.errors).length === 0;
    },

    async submit() {
        if (!this.validate()) return;

        this.submitting = true;

        try {
            const formData = new FormData();
            Object.keys(this.data).forEach(key => {
                if (this.data[key] !== null && this.data[key] !== '') {
                    formData.append(key, this.data[key]);
                }
            });

            const response = await fetch('/treasury/api/transactions/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
                body: formData,
            });

            if (response.ok) {
                this.$store.ui.notify('Transação criada com sucesso!', 'success');
                this.reset();
                this.$dispatch('transaction-created');
            } else {
                const data = await response.json();
                this.errors = data;
                this.$store.ui.notify('Erro ao criar transação', 'error');
            }
        } finally {
            this.submitting = false;
        }
    },

    reset() {
        this.data = {
            description: '',
            amount: '',
            is_positive: true,
            date: new Date().toISOString().split('T')[0],
            category: '',
            acquittance_doc: null,
        };
        this.errors = {};
    },
}));

// ============================================
// Modal de Fechamento de Período
// ============================================
Alpine.data('periodCloseModal', () => ({
    isOpen: false,
    period: null,
    notes: '',
    closing: false,
    preview: null,

    open(periodId) {
        const periodStore = this.$store.periods;
        this.period = periodStore.getById(periodId);
        this.isOpen = true;
        this.notes = '';
        this.preview = null;
    },

    close() {
        this.isOpen = false;
        this.period = null;
        this.notes = '';
        this.preview = null;
    },

    async previewClose() {
        if (!this.period) return;

        // Calcular preview do saldo final
        const summary = this.period.transactions_summary || { net: 0 };
        this.preview = this.period.opening_balance + summary.net;
    },

    async confirm() {
        if (!this.period || this.closing) return;

        this.closing = true;

        try {
            const result = await this.$store.periods.close(this.period.id, this.notes);
            this.$store.ui.notify(`Período fechado com sucesso! Saldo: ${formatBRL(result.closing_balance)}`, 'success');
            this.close();
            this.$dispatch('period-closed', { period: result.period });
        } catch (err) {
            this.$store.ui.notify('Erro ao fechar período: ' + err.message, 'error');
        } finally {
            this.closing = false;
        }
    },
}));

// ============================================
// Card de Período
// ============================================
Alpine.data('periodCard', (period) => ({
    period: period,
    showTransactions: false,
    loading: false,
    transactions: [],

    get statusClass() {
        switch (this.period.status) {
            case 'open': return 'border-l-4 border-l-yellow-400';
            case 'closed': return 'border-l-4 border-l-green-400';
            case 'archived': return 'border-l-4 border-l-gray-400';
            default: return '';
        }
    },

    get statusLabel() {
        switch (this.period.status) {
            case 'open': return 'Aberto';
            case 'closed': return 'Fechado';
            case 'archived': return 'Arquivado';
            default: return this.period.status;
        }
    },

    get statusColor() {
        switch (this.period.status) {
            case 'open': return 'text-yellow-600';
            case 'closed': return 'text-green-600';
            case 'archived': return 'text-gray-600';
            default: return '';
        }
    },

    toggleTransactions() {
        this.showTransactions = !this.showTransactions;
        if (this.showTransactions && this.transactions.length === 0) {
            this.loadTransactions();
        }
    },

    async loadTransactions() {
        this.loading = true;
        try {
            const response = await fetch(`/treasury/api/periods/${this.period.id}/transactions/`, {
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });
            this.transactions = await response.json();
        } finally {
            this.loading = false;
        }
    },

    formatBalance(balance) {
        return formatBRL(balance);
    },
}));

// ============================================
// Modal de Estorno
// ============================================
Alpine.data('reversalModal', () => ({
    isOpen: false,
    originalTransaction: null,
    data: {
        description: '',
        amount: '',
        is_positive: true,
        category: '',
        reason: '',
        authorized_by_id: null,
    },
    errors: {},
    submitting: false,

    get categories() {
        return this.$store.categories.categories || [];
    },

    open(transactionId) {
        this.$store.transactions.getById(transactionId).then(tx => {
            this.originalTransaction = tx;
            this.data = {
                description: tx.description,
                amount: tx.amount,
                is_positive: tx.is_positive,
                category: tx.category || '',
                reason: '',
                authorized_by_id: null,
            };
            this.isOpen = true;
            this.errors = {};
        });
    },

    close() {
        this.isOpen = false;
        this.originalTransaction = null;
        this.data = {
            description: '',
            amount: '',
            is_positive: true,
            category: '',
            reason: '',
            authorized_by_id: null,
        };
        this.errors = {};
    },

    validate() {
        this.errors = {};

        if (!this.data.reason.trim()) {
            this.errors.reason = 'O motivo do estorno é obrigatório.';
        }
        if (!this.data.amount || parseFloat(this.data.amount) <= 0) {
            this.errors.amount = 'O valor deve ser positivo.';
        }

        // Verificar se precisa de autorização
        if (this.originalTransaction?.period_status === 'archived' && !this.data.authorized_by_id) {
            this.errors.authorized_by_id = 'Estornos em períodos arquivados requerem autorização.';
        }

        return Object.keys(this.errors).length === 0;
    },

    async submit() {
        if (!this.validate()) return;

        this.submitting = true;

        try {
            const formData = new FormData();
            formData.append('original_transaction_id', this.originalTransaction.id);
            formData.append('description', this.data.description);
            formData.append('amount', this.data.amount);
            formData.append('is_positive', this.data.is_positive);
            if (this.data.category) formData.append('category_id', this.data.category);
            formData.append('reason', this.data.reason);
            if (this.data.authorized_by_id) {
                formData.append('authorized_by_id', this.data.authorized_by_id);
            }

            const response = await fetch('/treasury/api/reversals/create/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
                body: formData,
            });

            if (response.ok) {
                this.$store.ui.notify('Estorno criado com sucesso!', 'success');
                this.close();
                this.$dispatch('reversal-created');
            } else {
                const data = await response.json();
                this.errors = data;
                this.$store.ui.notify('Erro ao criar estorno', 'error');
            }
        } finally {
            this.submitting = false;
        }
    },
}));

// ============================================
// Filtros de Transação
// ============================================
Alpine.data('transactionFilters', () => ({
    filters: {
        period: null,
        category: null,
        is_positive: null,
        date_from: null,
        date_to: null,
        search: '',
    },

    get periods() {
        return this.$store.periods.periods || [];
    },

    get categories() {
        return this.$store.categories.categories || [];
    },

    init() {
        this.$store.periods.load();
        this.$store.categories.load();
    },

    apply() {
        this.$dispatch('apply-filters', { filters: this.filters });
    },

    clear() {
        this.filters = {
            period: null,
            category: null,
            is_positive: null,
            date_from: null,
            date_to: null,
            search: '',
        };
        this.$dispatch('apply-filters', { filters: this.filters });
    },
}));

// ============================================
// Dashboard Summary Card
// ============================================
Alpine.data('summaryCard', (options) => ({
    title: options.title || '',
    value: options.value || 0,
    icon: options.icon || null,
    color: options.color || 'blue',
    loading: options.loading || false,
    trend: options.trend || null,

    get colorClass() {
        const colors = {
            blue: 'bg-blue-500 text-blue-600',
            green: 'bg-green-500 text-green-600',
            red: 'bg-red-500 text-red-600',
            yellow: 'bg-yellow-500 text-yellow-600',
            purple: 'bg-purple-500 text-purple-600',
        };
        return colors[this.color] || colors.blue;
    },

    get formatValue() {
        if (typeof this.value === 'number') {
            return formatBRL(this.value);
        }
        return this.value;
    },

    get trendHtml() {
        if (!this.trend) return '';
        const isPositive = this.trend >= 0;
        const icon = isPositive ? '↑' : '↓';
        const color = isPositive ? 'text-green-600' : 'text-red-600';
        return `<span class="${color}">${icon} ${Math.abs(this.trend)}%</span>`;
    },
}));

// ============================================
// Categoria Manager (CRUD de categorias)
// ============================================
Alpine.data('categoryManager', () => ({
    categories: [],
    loading: false,
    editing: null,
    newName: '',
    showForm: false,

    init() {
        this.load();
    },

    async load() {
        this.loading = true;
        try {
            const response = await fetch('/treasury/api/categories/', {
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });
            this.categories = await response.json();
        } finally {
            this.loading = false;
        }
    },

    startCreate() {
        this.editing = null;
        this.newName = '';
        this.showForm = true;
    },

    startEdit(category) {
        this.editing = category.id;
        this.newName = category.name;
        this.showForm = true;
    },

    async save() {
        if (!this.newName.trim()) return;

        try {
            if (this.editing) {
                // Update
                const response = await fetch(`/treasury/api/categories/${this.editing}/`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ name: this.newName }),
                });

                if (response.ok) {
                    this.$store.ui.notify('Categoria atualizada!', 'success');
                    this.load();
                    this.showForm = false;
                }
            } else {
                // Create
                const response = await fetch('/treasury/api/categories/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ name: this.newName }),
                });

                if (response.ok) {
                    this.$store.ui.notify('Categoria criada!', 'success');
                    this.load();
                    this.showForm = false;
                }
            }
        } catch (err) {
            this.$store.ui.notify('Erro ao salvar categoria', 'error');
        }
    },

    cancel() {
        this.showForm = false;
        this.editing = null;
        this.newName = '';
    },

    async delete(id) {
        if (!confirm('Tem certeza que deseja excluir esta categoria?')) return;

        try {
            const response = await fetch(`/treasury/api/categories/${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });

            if (response.ok) {
                this.$store.ui.notify('Categoria excluída!', 'success');
                this.load();
            }
        } catch (err) {
            this.$store.ui.notify('Erro ao excluir categoria', 'error');
        }
    },
}));

// ============================================
// Helper Functions (globais)
// ============================================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatBRL(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    }).format(value);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}
