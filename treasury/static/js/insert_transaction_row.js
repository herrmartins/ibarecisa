import { formatCurrency } from "./format_currency.js";
import { formatDate } from "./format_date.js";

export function insertTransactionRow(transaction, tableBody) {
	if (!transaction) {
		console.error("Transaction is undefined or null:", transaction);
		return;
	}

	const row = document.createElement("tr");

	const dateCell = document.createElement("td");
	const descriptionCell = document.createElement("td");
	const amountCell = document.createElement("td");
	const balanceCell = document.createElement("td");
	const operationsCell = document.createElement("td");

	const category =
		typeof transaction.category === "object"
			? transaction.category.name
			: transaction.category;

	dateCell.textContent = formatDate(transaction.date);
	descriptionCell.textContent = `${transaction.description} - ${category}`;
	amountCell.textContent = formatCurrency(transaction.amount);
	balanceCell.textContent = formatCurrency(transaction.current_balance);
	operationsCell.innerHTML = `<a href="/treasury/transaction/${transaction.id}" class="btn btn-light btn-sm edit-button" data-id="${transaction.id}">&#x270D;</a>`;

	if (transaction.amount >= 0) {
		amountCell.classList.add("text-primary");
	} else {
		amountCell.classList.add("text-danger");
	}

	row.appendChild(dateCell);
	row.appendChild(descriptionCell);
	row.appendChild(amountCell);
	row.appendChild(balanceCell);
	row.appendChild(operationsCell);

	// Insert the row at the beginning of the table body
	if (tableBody.firstChild) {
		tableBody.insertBefore(row, tableBody.firstChild);
	} else {
		tableBody.appendChild(row);
	}
}
