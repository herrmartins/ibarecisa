/**
 * Alpine.js Stores para o módulo de Tesouraria
 *
 * Implementa stores globais para gerenciar:
 * - Períodos contábeis
 * - Transações
 * - Categorias
 * - UI (loading, notifications, etc.)
 */

// ============================================
// Helper Functions (definidos antes dos stores)
// ============================================

/**
 * Obtém o CSRF token do cookie
 */
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

document.addEventListener('alpine:init', () => {
    // ============================================
    // Store de Períodos
    // ============================================
    Alpine.store('periods', {
        periods: [],
        currentPeriod: null,
        loading: false,
        error: null,

        // Carregar todos os períodos
        async load() {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch('/treasury/api/periods/', {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) throw new Error('Falha ao carregar períodos');

                const data = await response.json();
                this.periods = data.results || data;
            } catch (err) {
                this.error = err.message;
                console.error('Erro ao carregar períodos:', err);
            } finally {
                this.loading = false;
            }
        },

        // Carregar período atual
        async loadCurrent() {
            try {
                const response = await fetch('/treasury/api/periods/current/', {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) {
                    if (response.status === 404) {
                        this.currentPeriod = null;
                        return;
                    }
                    throw new Error('Falha ao carregar período atual');
                }

                this.currentPeriod = await response.json();
            } catch (err) {
                console.error('Erro ao carregar período atual:', err);
            }
        },

        // Fechar período
        async close(periodId, notes = '') {
            try {
                const response = await fetch(`/treasury/api/periods/${periodId}/close/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ notes }),
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Falha ao fechar período');
                }

                const data = await response.json();

                // Atualizar a lista de períodos
                await this.load();

                return data;
            } catch (err) {
                console.error('Erro ao fechar período:', err);
                throw err;
            }
        },

        // Reabrir período
        async reopen(periodId) {
            try {
                const response = await fetch(`/treasury/api/periods/${periodId}/reopen/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Falha ao reabrir período');
                }

                await this.load();
                return await response.json();
            } catch (err) {
                console.error('Erro ao reabrir período:', err);
                throw err;
            }
        },

        // Arquivar período
        async archive(periodId) {
            try {
                const response = await fetch(`/treasury/api/periods/${periodId}/archive/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Falha ao arquivar período');
                }

                await this.load();
                return await response.json();
            } catch (err) {
                console.error('Erro ao arquivar período:', err);
                throw err;
            }
        },

        // Buscar período por ID
        getById(id) {
            return this.periods.find(p => p.id === parseInt(id));
        },

        // Buscar período por mês
        getByMonth(year, month) {
            return this.periods.find(p => p.year === year && p.month_number === month);
        },
    });

    // ============================================
    // Store de Transações
    // ============================================
    Alpine.store('transactions', {
        transactions: [],
        currentTransaction: null,
        loading: false,
        error: null,
        filters: {
            period_id: null,
            category: null,
            is_positive: null,
            date_from: null,
            date_to: null,
            search: '',
        },
        pagination: {
            count: 0,
            next: null,
            previous: null,
            page: 1,
        },

        // Carregar transações com filtros
        async load(page = 1) {
            this.loading = true;
            this.error = null;

            try {
                const params = new URLSearchParams();
                if (this.filters.period_id) params.append('accounting_period', this.filters.period_id);
                if (this.filters.category) params.append('category', this.filters.category);
                if (this.filters.is_positive !== null) params.append('is_positive', this.filters.is_positive);
                if (this.filters.date_from) params.append('date_from', this.filters.date_from);
                if (this.filters.date_to) params.append('date_to', this.filters.date_to);
                if (this.filters.search) params.append('search', this.filters.search);
                params.append('page', page);

                const response = await fetch(`/treasury/api/transactions/?${params}`, {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) throw new Error('Falha ao carregar transações');

                const data = await response.json();
                this.transactions = data.results || data;
                this.pagination = {
                    count: data.count,
                    next: data.next,
                    previous: data.previous,
                    page: page,
                };
            } catch (err) {
                this.error = err.message;
                console.error('Erro ao carregar transações:', err);
            } finally {
                this.loading = false;
            }
        },

        // Criar nova transação
        async create(data) {
            try {
                const formData = new FormData();
                Object.keys(data).forEach(key => {
                    if (data[key] !== null && data[key] !== undefined) {
                        formData.append(key, data[key]);
                    }
                });

                const response = await fetch('/treasury/api/transactions/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: formData,
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || data.error || 'Falha ao criar transação');
                }

                const result = await response.json();

                // Recarregar lista
                await this.load();

                return result;
            } catch (err) {
                console.error('Erro ao criar transação:', err);
                throw err;
            }
        },

        // Atualizar transação
        async update(id, data) {
            try {
                const formData = new FormData();
                Object.keys(data).forEach(key => {
                    if (data[key] !== null && data[key] !== undefined) {
                        formData.append(key, data[key]);
                    }
                });

                const response = await fetch(`/treasury/api/transactions/${id}/`, {
                    method: 'PATCH',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: formData,
                });

                if (!response.ok) {
                    const result = await response.json();
                    throw new Error(result.detail || result.error || 'Falha ao atualizar transação');
                }

                const result = await response.json();

                // Recarregar lista
                await this.load();

                return result;
            } catch (err) {
                console.error('Erro ao atualizar transação:', err);
                throw err;
            }
        },

        // Deletar transação
        async delete(id) {
            try {
                const response = await fetch(`/treasury/api/transactions/${id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Falha ao deletar transação');
                }

                // Recarregar lista
                await this.load();
            } catch (err) {
                console.error('Erro ao deletar transação:', err);
                throw err;
            }
        },

        // Buscar transação por ID
        async getById(id) {
            try {
                const response = await fetch(`/treasury/api/transactions/${id}/`, {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) throw new Error('Falha ao carregar transação');

                this.currentTransaction = await response.json();
                return this.currentTransaction;
            } catch (err) {
                console.error('Erro ao carregar transação:', err);
                throw err;
            }
        },

        // Limpar filtros
        clearFilters() {
            this.filters = {
                period_id: null,
                category: null,
                is_positive: null,
                date_from: null,
                date_to: null,
                search: '',
            };
        },

        // Definir filtro de período
        setPeriodFilter(periodId) {
            this.filters.period_id = periodId;
            this.load();
        },
    });

    // ============================================
    // Store de Categorias
    // ============================================
    Alpine.store('categories', {
        categories: [],
        loading: false,
        error: null,

        // Carregar categorias
        async load() {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch('/treasury/api/categories/', {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) throw new Error('Falha ao carregar categorias');

                const data = await response.json();
                this.categories = data.results || data;
            } catch (err) {
                this.error = err.message;
                console.error('Erro ao carregar categorias:', err);
            } finally {
                this.loading = false;
            }
        },

        // Criar nova categoria
        async create(name) {
            try {
                const response = await fetch('/treasury/api/categories/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ name }),
                });

                if (!response.ok) throw new Error('Falha ao criar categoria');

                await this.load();
                return await response.json();
            } catch (err) {
                console.error('Erro ao criar categoria:', err);
                throw err;
            }
        },

        // Buscar categoria por ID
        getById(id) {
            return this.categories.find(c => c.id === parseInt(id));
        },

        // Buscar categoria por nome
        getByName(name) {
            return this.categories.find(c => c.name === name);
        },
    });

    // ============================================
    // Store de Relatórios
    // ============================================
    Alpine.store('reports', {
        currentBalance: null,
        monthlyReport: null,
        loading: false,
        error: null,

        // Carregar saldo atual
        async loadCurrentBalance() {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch('/treasury/api/reports/current-balance/', {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) throw new Error('Falha ao carregar saldo atual');

                this.currentBalance = await response.json();
            } catch (err) {
                this.error = err.message;
                console.error('Erro ao carregar saldo atual:', err);
            } finally {
                this.loading = false;
            }
        },

        // Carregar relatório mensal
        async loadMonthlyReport(year, month) {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch(`/treasury/api/reports/monthly/${year}/${month}/`, {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) throw new Error('Falha ao carregar relatório mensal');

                this.monthlyReport = await response.json();
            } catch (err) {
                this.error = err.message;
                console.error('Erro ao carregar relatório mensal:', err);
            } finally {
                this.loading = false;
            }
        },

        // Carregar saldo de período específico
        async loadPeriodBalance(year, month) {
            try {
                const response = await fetch(`/treasury/api/reports/balance/${year}/${month}/`, {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) throw new Error('Falha ao carregar saldo do período');

                return await response.json();
            } catch (err) {
                console.error('Erro ao carregar saldo do período:', err);
                throw err;
            }
        },
    });

    // ============================================
    // Store de Estornos
    // ============================================
    Alpine.store('reversals', {
        reversals: [],
        loading: false,
        error: null,

        // Carregar estornos de uma transação
        async loadByTransaction(transactionId) {
            try {
                const response = await fetch(`/treasury/api/transactions/${transactionId}/reversals/`, {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (!response.ok) throw new Error('Falha ao carregar estornos');

                this.reversals = await response.json();
            } catch (err) {
                this.error = err.message;
                console.error('Erro ao carregar estornos:', err);
                throw err;
            }
        },

        // Criar estorno
        async create(data) {
            try {
                const formData = new FormData();
                Object.keys(data).forEach(key => {
                    if (data[key] !== null && data[key] !== undefined) {
                        formData.append(key, data[key]);
                    }
                });

                const response = await fetch('/treasury/api/reversals/create/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: formData,
                });

                if (!response.ok) {
                    const result = await response.json();
                    throw new Error(result.error || 'Falha ao criar estorno');
                }

                return await response.json();
            } catch (err) {
                console.error('Erro ao criar estorno:', err);
                throw err;
            }
        },
    });

    // ============================================
    // Store de UI da Tesouraria (loading, notifications, modals)
    // ============================================
    Alpine.store('treasuryUi', {
        notifications: [],
        loading: false,
        modalOpen: false,
        modalContent: null,

        // OCR Modal state
        ocrModalOpen: false,
        ocrProcessing: false,
        ocrResult: null,
        ocrError: null,
        ocrPreviewImage: null,
        ocrFile: null,  // Arquivo original para anexar ao formulário

        // Mostrar notificação
        notify(message, type = 'info') {
            const id = Date.now();
            this.notifications.push({ id, message, type });

            // Auto-remove após diferentes tempos dependendo do tipo
            const duration = type === 'error' ? 0 : 5000; // Erros só fecham manualmente
            if (duration > 0) {
                setTimeout(() => {
                    this.removeNotification(id);
                }, duration);
            }
        },

        // Remover notificação
        removeNotification(id) {
            this.notifications = this.notifications.filter(n => n.id !== id);
        },

        // Limpar todas as notificações
        clearNotifications() {
            this.notifications = [];
        },

        // Abrir modal
        openModal(content) {
            this.modalContent = content;
            this.modalOpen = true;
        },

        // Fechar modal
        closeModal() {
            this.modalOpen = false;
            this.modalContent = null;
        },

        // Mostrar loading
        showLoading() {
            this.loading = true;
        },

        // Esconder loading
        hideLoading() {
            this.loading = false;
        },

        // Open OCR modal
        openOcrModal() {
            this.ocrModalOpen = true;
            this.ocrResult = null;
            this.ocrError = null;
            this.ocrPreviewImage = null;
        },

        // Close OCR modal
        closeOcrModal() {
            this.ocrModalOpen = false;
            this.ocrResult = null;
            this.ocrError = null;
            this.ocrPreviewImage = null;
            this.ocrProcessing = false;
            this.ocrFile = null;  // Limpar arquivo
        },
    });
});

// ============================================
// Helper Functions (formatação)
// ============================================

/**
 * Formata valor para BRL
 */
function formatBRL(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    }).format(value);
}

/**
 * Formata data para PT-BR
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

/**
 * Formata data e hora para PT-BR
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
}

// ============================================
// Expor helpers globalmente (para uso no modal)
// ============================================

window.formatBRL = formatBRL;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;

// ============================================
// OCR Handlers (globais para acesso do modal)
// ============================================

window.ocrHandlers = {
    /**
     * Manipula seleção de arquivo no modal OCR
     */
    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        const store = Alpine.store('treasuryUi');

        // Validar tamanho (10MB)
        if (file.size > 10 * 1024 * 1024) {
            store.ocrError = 'Arquivo muito grande. Máximo: 10MB';
            return;
        }

        // Mostrar preview
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                store.ocrPreviewImage = e.target.result;
            };
            reader.readAsDataURL(file);
        } else {
            store.ocrPreviewImage = null;
        }

        // Salvar arquivo para anexar depois
        store.ocrFile = file;
        store.ocrError = null;

        // Enviar para OCR
        await this.processOcr(file);
    },

    /**
     * Processa arquivo via API OCR
     */
    async processOcr(file) {
        const store = Alpine.store('treasuryUi');
        store.ocrProcessing = true;
        store.ocrError = null;

        console.log('[OCR] Iniciando processamento:', file.name, file.size, 'bytes');

        const formData = new FormData();
        formData.append('receipt', file);

        try {
            console.log('[OCR] Enviando para API...');
            const response = await fetch('/treasury/api/ocr/receipt/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: formData
            });

            console.log('[OCR] Resposta recebida:', response.status);
            const data = await response.json();
            console.log('[OCR] Dados recebidos:', data);

            if (response.ok && data.description) {
                store.ocrResult = data;
                console.log('[OCR] ✅ Sucesso:', data);
            } else {
                store.ocrError = data.error || 'Erro ao processar imagem';
                console.error('[OCR] ❌ Erro:', data.error || data);
            }
        } catch (error) {
            console.error('[OCR] ❌ Erro de comunicação:', error);
            store.ocrError = 'Erro ao comunicar com servidor';
        } finally {
            store.ocrProcessing = false;
            console.log('[OCR] Processamento finalizado');
        }
    },

    /**
     * Aplica resultado OCR ao formulário
     */
    applyResult() {
        const store = Alpine.store('treasuryUi');
        const result = store.ocrResult;

        if (!result) return;

        // Encontrar componente - tenta transactionForm ou transactionUpdate
        let transactionForm = Alpine.$data(document.querySelector('[x-data*="transactionForm"]'));
        if (!transactionForm) {
            transactionForm = Alpine.$data(document.querySelector('[x-data*="transactionUpdate"]'));
        }
        if (!transactionForm) {
            console.error('transactionForm or transactionUpdate not found');
            return;
        }

        // Aplicar dados ao formulário
        transactionForm.form.description = result.description || '';
        transactionForm.form.amount = result.amount?.toString() || '';
        transactionForm.form.date = result.date || new Date().toISOString().split('T')[0];
        transactionForm.form.is_positive = result.is_positive !== false;
        transactionForm.form.category = result.category_id || '';

        // Atualizar display de amount (se existir no componente de criação)
        if (transactionForm.amountDisplay !== undefined) {
            transactionForm.amountDisplay = result.amount?.toString() || '';
        }

        // Anexar arquivo ao input do formulário
        if (store.ocrFile && transactionForm.$refs.docFile) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(store.ocrFile);
            transactionForm.$refs.docFile.files = dataTransfer.files;
        }

        // Fechar modal
        store.closeOcrModal();

        store.notify('Dados aplicados ao formulário!', 'success');
    },

    /**
     * Helper para pegar cookie CSRF
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
};
