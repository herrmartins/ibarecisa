import { formatCurrency } from "./format_currency.js";
import { formatDate } from "./format_date.js";

export async function getTransactions(month, year) {
	try {
		const fetchResponse = await fetch(
			`/treasury/transactions/?month=${month}&year=${year}`,
			{
				headers: {
					"X-Requested-With": "XMLHttpRequest",
				},
			},
		);

		if (!fetchResponse.ok) {
			throw new Error(`Erro... Resposta da rede: ${fetchResponse.statusText}`);
		}

		const fetchResult = await fetchResponse.json();

		const transactionsTableBody = document.querySelector(
			"#transactionsTable tbody",
		);
		transactionsTableBody.innerHTML = "";

		// biome-ignore lint/complexity/noForEach: <explanation>
		fetchResult.transactions.forEach((transaction) => {
			const row = transactionsTableBody.insertRow();

			const dateCell = row.insertCell(0);
			const descriptionCell = row.insertCell(1);
			const amountCell = row.insertCell(2);
			const balanceCell = row.insertCell(3);
			const operationsCell = row.insertCell(4);

			dateCell.textContent = formatDate(transaction.date);
			descriptionCell.textContent = transaction.description;
			amountCell.textContent = formatCurrency(transaction.amount);
			balanceCell.textContent = formatCurrency(transaction.current_balance);
			operationsCell.innerHTML = `<a href="/treasury/transaction/${transaction.id}" class="btn btn-light btn-sm edit-button grid-item" data-id="${transaction.id}">&#x270D;</a>`;

			if (transaction.amount >= 0) {
				amountCell.classList.add("text-primary");
			} else {
				amountCell.classList.add("text-danger");
			}
		});

		document.getElementById("currentBalance").textContent = formatCurrency(
			fetchResult.current_balance,
		);
		document.getElementById("currentAnawareBalance").textContent =
			formatCurrency(fetchResult.monthly_result);
		document.getElementById("positive_transactions").textContent =
			formatCurrency(fetchResult.positive_transactions);
		document.getElementById("negative_transactions").textContent =
			formatCurrency(fetchResult.negative_transactions);

		// Update the previous month's balance
		document.querySelector(".bg-success .fw-light").textContent =
			formatCurrency(fetchResult.previous_month_balance);

		const currentMonthYearElement = document.getElementById("currentMonthYear");
		if (currentMonthYearElement) {
			currentMonthYearElement.textContent = `${month} ${year}`;
		}

		const prevMonthLink = document.getElementById("prevMonthLink");
		if (prevMonthLink) {
			prevMonthLink.href = `?month=${month - 1 || 12}&year=${
				month - 1 ? year : year - 1
			}`;
		}

		const nextMonthLink = document.getElementById("nextMonthLink");
		if (nextMonthLink) {
			nextMonthLink.href = `?month=${(month % 12) + 1}&year=${
				month % 12 ? year : year + 1
			}`;
		}

		const today = new Date();
		const currentMonth = today.getMonth() + 1;
		const currentYear = today.getFullYear();
		const saldoLabel = document.getElementById("saldoLabel");

		if (month === currentMonth && year === currentYear) {
			saldoLabel.textContent = "Saldo Corrente";
		} else {
			saldoLabel.textContent = "Saldo do Mês";
		}
	} catch (error) {
		console.error("Ocorreu um erro ao receber as transações:", error);
		alert("Ocorreu um erro ao receber as transações. Tente novamente...");
	}
}
