import { formatCurrency } from './format_currency.js';
import { formatDate } from './format_date.js';

export async function getTransactions(year, month) {
    try {
        const response = await fetch(`/treasury/transactions/?year=${year}&month=${month}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        });

        if (!response.ok) {
            throw new Error(`Erro... Resposta da rede: ${response.statusText}`);
        }

        const data = await response.json();
        const transactionsTable = document.getElementById('transactionsTable');
        const transactionsTableBody = document.querySelector('#transactionsTable tbody');
        const noTransactionsMessage = document.getElementById('noTransactionsMessage');

        // Clear the table body
        transactionsTableBody.innerHTML = '';

        if (data.transactions.length === 0) {
            // If there are no transactions, hide the table and show the message
            transactionsTable.style.display = 'none';
            noTransactionsMessage.style.display = 'block';
        } else {
            // If there are transactions, show the table and hide the message
            transactionsTable.style.display = 'table';
            noTransactionsMessage.style.display = 'none';

            // biome-ignore lint/complexity/noForEach: <explanation>
            data.transactions.forEach((transaction) => {
                const row = transactionsTableBody.insertRow();

                const dateCell = row.insertCell(0);
                const descriptionCell = row.insertCell(1);
                const amountCell = row.insertCell(2);
                const balanceCell = row.insertCell(3);
                const operationsCell = row.insertCell(4);

                dateCell.textContent = formatDate(transaction.date);
                descriptionCell.textContent = `${transaction.description} - ${transaction.category}`;
                amountCell.textContent = formatCurrency(transaction.amount);
                balanceCell.textContent = formatCurrency(transaction.current_balance);
                operationsCell.innerHTML = `<a href="/treasury/transaction/${transaction.id}" class="btn btn-light btn-sm edit-button" data-id="${transaction.id}">&#x270D;</a>`;

                if (transaction.amount >= 0) {
                    amountCell.classList.add('text-primary');
                } else {
                    amountCell.classList.add('text-danger');
                }
            });
        }

        document.getElementById('currentBalance').textContent = formatCurrency(data.current_balance);
        document.getElementById('currentAnawareBalance').textContent = formatCurrency(data.monthly_result);
        document.getElementById('positive_transactions').textContent = formatCurrency(data.positive_transactions);
        document.getElementById('negative_transactions').textContent = formatCurrency(data.negative_transactions);
        document.querySelector('.bg-success .fw-light').textContent = formatCurrency(data.previous_month_balance);

        const today = new Date();
        const currentMonth = today.getMonth() + 1;
        const currentYear = today.getFullYear();
        const saldoLabel = document.getElementById('saldoLabel');

        if (Number.parseInt(month) === currentMonth && Number.parseInt(year) === currentYear) {
            saldoLabel.textContent = 'Saldo Corrente';
        } else {
            saldoLabel.textContent = 'Saldo do Mês';
        }

    } catch (error) {
        console.error('Ocorreu um erro ao receber as transações:', error);
        alert('Ocorreu um erro ao receber as transações. Tente novamente...');
    }
}

