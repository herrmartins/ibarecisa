import { getTransactions } from "./get_transactions.js";
import { insertTransactionRow } from "./insert_transaction_row.js";

async function addTransaction(event) {
	event.preventDefault();
	const selectedYear = document.getElementById("yearSelect");
	const selectedMonth = document.getElementById("monthSelect");

	const form = event.target;
	const formData = new FormData(form);

	const formDateObject = new Date(formData.get("date"));
	const formYear = formDateObject.getFullYear();
	const formMonth = formDateObject.getMonth() + 1;

	const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

	try {
		const response = await fetch("/treasury/add-transaction/", {
			method: "POST",
			headers: {
				"X-CSRFToken": csrfToken,
			},
			body: formData,
		});

		const contentType = response.headers.get("content-type");
		if (!contentType || !contentType.includes("application/json")) {
			const errorText = await response.text();
			throw new Error(`Response format is not JSON: ${errorText}`);
		}

		const result = await response.json();

		console.log("Transaction response:", result);

		if (result.success) {
			if (
				formYear === Number.parseInt(selectedYear.value) &&
				formMonth === Number.parseInt(selectedMonth.value)
			) {
				const transactionsTableBody = document.querySelector(
					"#transactionsTable tbody",
				);

				insertTransactionRow(result.transaction, transactionsTableBody);
			} else {
				selectedYear.value = result.year;
				selectedMonth.value = result.month;
				getTransactions(result.year, result.month);
			}
		} else {
			console.error("Error adding transaction:", result.errors);
			alert(`Error adding transaction: ${JSON.stringify(result.errors)}`);
		}
	} catch (error) {
		console.error("An error occurred:", error);
		alert("An error occurred. Please try again.");
	}
}

window.addTransaction = addTransaction;
