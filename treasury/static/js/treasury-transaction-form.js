/**
 * Alpine.js Component: Transaction Form
 *
 * Componente para formulário de criação de transações
 * - Suporta adição em massa com "Salvar e Continuar"
 * - Mostra transações da sessão e do dia
 * - Exibe evolução do saldo
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('transactionForm', () => ({
        form: {
            is_positive: true,
            date: new Date().toISOString().split('T')[0],
            description: '',
            amount: '',
            category: ''
        },
        amountDisplay: '',
        categories: [],
        submitting: false,
        errors: [],

        // Transações da sessão (adicionadas agora)
        sessionTransactions: [],

        // Transações do dia selecionado
        dayTransactions: [],

        // Totais do dia
        dayTotals: {
            opening_balance: 0,
            total_positive: 0,
            total_negative: 0,
            closing_balance: 0,
            count: 0
        },

        // Loading state para transações do dia
        loadingDayTransactions: false,

        // Mobile bottom sheet state
        mobileSheetOpen: false,

        // Atalho Ctrl+Enter
        init() {
            this.loadCategories();
            this.loadDayTransactions();

            // Atalho Ctrl+Enter para salvar
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    e.preventDefault();
                    this.submit(true); // true = salvar e continuar
                }
            });

            // Watch para mudança de data
            this.$watch('form.date', () => {
                this.loadDayTransactions();
            });
        },

        async loadCategories() {
            try {
                const response = await fetch('/treasury/api/categories/', {
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                });
                const data = await response.json();
                this.categories = data.results || data;
            } catch (error) {
                console.error('Error loading categories:', error);
            }
        },

        async loadDayTransactions() {
            if (!this.form.date) return;

            this.loadingDayTransactions = true;
            try {
                const date = new Date(this.form.date);
                const year = date.getFullYear();
                const month = date.getMonth() + 1;
                const day = date.getDate();

                // Buscar transações do dia
                const response = await fetch(`/treasury/api/transactions/?date_from=${this.form.date}&date_to=${this.form.date}&page_size=100`, {
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                });

                if (response.ok) {
                    const data = await response.json();
                    this.dayTransactions = data.results || [];

                    // Calcular totais do dia
                    this.calculateDayTotals();
                }
            } catch (error) {
                console.error('Error loading day transactions:', error);
            } finally {
                this.loadingDayTransactions = false;
            }
        },

        async calculateDayTotals() {
            try {
                // Buscar saldo inicial (último fechamento antes desta data)
                const date = new Date(this.form.date);
                const yesterday = new Date(date);
                yesterday.setDate(yesterday.getDate() - 1);

                // Tenta buscar o balance do dia anterior
                const year = date.getFullYear();
                const month = date.getMonth() + 1;

                const balanceResponse = await fetch(`/treasury/api/reports/monthly/${year}/${month}/`, {
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                });

                let openingBalance = 0;
                if (balanceResponse.ok) {
                    const balanceData = await balanceResponse.json();
                    openingBalance = balanceData.summary?.opening_balance || 0;
                }

                // Calcular totais
                const positive = this.dayTransactions
                    .filter(t => t.is_positive)
                    .reduce((sum, t) => sum + parseFloat(t.amount), 0);

                const negative = this.dayTransactions
                    .filter(t => !t.is_positive)
                    .reduce((sum, t) => sum + parseFloat(t.amount), 0);

                this.dayTotals = {
                    opening_balance: openingBalance,
                    total_positive: positive,
                    total_negative: Math.abs(negative),
                    closing_balance: openingBalance + positive - Math.abs(negative),
                    count: this.dayTransactions.length
                };
            } catch (error) {
                console.error('Error calculating totals:', error);
            }
        },

        updateAmountFromDisplay() {
            const value = this.amountDisplay.trim();
            if (value.startsWith('-')) {
                this.form.is_positive = false;
                this.form.amount = value.substring(1);
            } else {
                this.form.is_positive = true;
                this.form.amount = value;
            }
        },

        get hasErrors() {
            return this.errors.length > 0;
        },

        get sessionCount() {
            return this.sessionTransactions.length;
        },

        get todayCount() {
            const today = new Date().toISOString().split('T')[0];
            return this.sessionTransactions.filter(t => t.date === today).length;
        },

        formatAmount(value) {
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(value);
        },

        formatDate(dateStr) {
            const date = new Date(dateStr + 'T00:00:00');
            return date.toLocaleDateString('pt-BR');
        },

        formatTime(dateStr) {
            const date = new Date(dateStr);
            return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        },

        async submit(continueAdding = false) {
            this.errors = [];
            this.submitting = true;

            // Validation
            if (!this.form.description) {
                this.errors.push('Descrição é obrigatória');
            }
            if (!this.form.amount || parseFloat(this.form.amount) <= 0) {
                this.errors.push('Valor deve ser maior que zero');
            }
            if (!this.form.date) {
                this.errors.push('Data é obrigatória');
            }

            if (this.hasErrors) {
                this.submitting = false;
                return;
            }

            // Prepare form data
            const formData = new FormData();
            formData.append('description', this.form.description);
            formData.append('amount', this.form.amount);
            formData.append('is_positive', this.form.is_positive);
            formData.append('date', this.form.date);
            if (this.form.category) {
                formData.append('category', this.form.category);
            }

            const docFile = this.$refs.docFile?.files[0];
            if (docFile) {
                formData.append('acquittance_doc', docFile);
            }

            try {
                const response = await fetch('/treasury/api/transactions/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: formData
                });

                if (response.ok) {
                    const result = await response.json();

                    // Adicionar à lista da sessão
                    this.sessionTransactions.unshift({
                        ...result,
                        temp: true // marca como recém-adicionada
                    });

                    // Atualizar transações do dia
                    await this.loadDayTransactions();

                    if (continueAdding) {
                        // Limpar formulário e continuar
                        this.form.description = '';
                        this.form.amount = '';
                        this.amountDisplay = '';
                        this.form.category = '';
                        this.$refs.docFile && (this.$refs.docFile.value = '');

                        this.$store.treasuryUi.notify(
                            `✓ ${this.todayCount}ª transação hoje adicionada!`,
                            'success'
                        );
                    } else {
                        // Redirecionar para lista
                        this.$store.treasuryUi.notify('Transação criada com sucesso!', 'success');
                        window.location.href = '/treasury/transacoes/';
                    }
                } else {
                    // Tentar parsear JSON, mas pode vir HTML em caso de erro 500
                    const contentType = response.headers.get('content-type');
                    let errorData;
                    if (contentType && contentType.includes('application/json')) {
                        errorData = await response.json();
                        this.errors = Object.values(errorData).flat();
                    } else {
                        // Resposta não é JSON (provavelmente HTML de erro)
                        const text = await response.text();
                        console.error('Server returned non-JSON response:', text.substring(0, 500));
                        this.errors = [`Erro ${response.status}: ${response.statusText}`];
                    }
                }
            } catch (error) {
                this.errors = ['Erro ao criar transação. Tente novamente.'];
                console.error('Request failed:', error);
            } finally {
                this.submitting = false;
            }
        },

        getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
        }
    }));
});
