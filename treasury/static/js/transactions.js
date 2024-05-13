import { getCookie } from "./get_cookie.js";

function loadTransactionData() {
	const currentBalanceElement = document.getElementById("currentBalance");
	const currentAnawareBalanceElement = document.getElementById(
		"currentAnawareBalance",
	);
	const positiveTransactionsElement = document.getElementById(
		"positive_transactions",
	);
	const negativeTransactionsElement = document.getElementById(
		"negative_transactions",
	);
	const transactionsTableBody = document.querySelector(
		"#transactions_list table tbody",
	);
	const deleteButtons = document.querySelectorAll(".delete-button");
	const formTransactionElement = document.getElementById("transaction_form");
	let currentBalance = 0;

	fetch("http://127.0.0.1:8000/api/getbalance")
		.then((response) => {
			if (response.ok) {
				return response.json();
			}
				throw new Error("Erro ao executar o fetch do saldo...");
		})
		.then((data) => {
			currentBalanceElement.innerText = formatCurrency(data.current_balance);
			currentBalance = parseFloat(data.last_month_balance);
			currentAnawareBalanceElement.innerText = formatCurrency(
				data.unaware_month_balance,
			);
			positiveTransactionsElement.innerText = formatCurrency(
				data.sum_positive_transactions,
			);
			negativeTransactionsElement.innerText = formatCurrency(
				data.sum_negative_transactions,
			);

			fetch("http://127.0.0.1:8000/api/transactions")
				.then((response) => {
					if (response.ok) {
						return response.json();
					}
					throw new Error("Erro ao executar o fetch.");
				})
				.then((data) => {
					let currentBalanceTrack = parseFloat(currentBalance);
					transactionsTableBody.innerHTML = "";
					// biome-ignore lint/complexity/noForEach: <explanation>
					data.forEach((item) => {
						const row = transactionsTableBody.insertRow();
						const dateCell = row.insertCell(0);
						const descriptionCell = row.insertCell(1);
						const valueCell = row.insertCell(2);
						const currentBalanceCell = row.insertCell(3);
						const operationsCell = row.insertCell(4);

						const dateObj = new Date(`${item.date}T00:00:00Z`);
						const offset = dateObj.getTimezoneOffset();
						dateObj.setMinutes(dateObj.getMinutes() + offset);

						const formattedDate = dateObj.toLocaleDateString("pt-BR");

						dateCell.textContent = formattedDate;

						descriptionCell.textContent =
							`${item.category.name} - ${item.description}`;

						if (item.amount >= 0) {
							valueCell.textContent = formatCurrency(item.amount);
							valueCell.classList.add("text-primary");
						} else {
							valueCell.textContent = formatCurrency(item.amount);
							valueCell.classList.add("text-danger");
						}

						currentBalanceTrack += parseFloat(item.amount);
						currentBalanceCell.textContent =
							formatCurrency(currentBalanceTrack);
						operationsCell.innerHTML = `
                            <a href="/treasury/transaction/${item.id}" class="btn btn-light btn-sm edit-button grid-item" data-id="${item.id}">&#x270D;</a>
                        `;
					});
					const deleteButtons = document.querySelectorAll(".delete-button");
					const editButtons = document.querySelectorAll(".edit-button");
					// biome-ignore lint/complexity/noForEach: <explanation>
					deleteButtons.forEach((button) => {
						button.addEventListener("click", (event) => {
							const itemId = event.target.dataset.id;
							deleteTransaction(itemId);
						});
					});
					// biome-ignore lint/complexity/noForEach: <explanation>
					editButtons.forEach((button) => {
						button.addEventListener("click", (event) => {
							const itemId = event.target.dataset.id;
							window.location.href = `/treasury/transaction/${itemId}`;
						});
					});
					const lastRow = transactionsTableBody.insertRow();
					const lastDateCell = lastRow.insertCell(0);
					const lastDescriptionCell = lastRow.insertCell(1);
					const lastValueCell = lastRow.insertCell(2);
					const lastTrackBalanceCell = lastRow.insertCell(3);
					const lastOperationsCell = lastRow.insertCell(4);

					lastDateCell.innerText = "-";
					lastDescriptionCell.innerText = "-";
					lastValueCell.innerHTML = '<div class="fw-bold">Saldo Atual:</div>';
					lastTrackBalanceCell.textContent =
						formatCurrency(currentBalanceTrack);
					lastOperationsCell.innerText = "";
				})
				.catch((error) => {
					showDynamicMessage("Erro: ", error, "alert-danger");
				});
		})
		.catch((error) => {
			console.error("Erro ao executar o fetch:", error);
		});
}

async function deleteTransaction(id) {
	const csrfToken = getCookie("csrftoken");
	const headers = {
		// "Content-Type": "application/json",
		"X-CSRFToken": csrfToken,
	};
	try {
		const response = await fetch(
			`http://127.0.0.1:8000/api/transaction/${id}/delete/`,
			{
				method: "DELETE",
				headers: headers,
			},
		);

		if (response.ok) {
			showDynamicMessage("Transação deletada...", "alert-success");
			loadTransactionData();
		} else {
			showDynamicMessage("Falha ao deletar a transação...", "alert-danger");
		}
	} catch (error) {
		showDynamicMessage("Erro: ", error, "alert-danger");
	}
}

function formatCurrency(amount) {
	return new Intl.NumberFormat("pt-BR", {
		style: "currency",
		currency: "BRL",
	}).format(amount);
}

const apiTransactionUrl = "http://127.0.0.1:8000/api/transactions/post";

const form = document.getElementById("transaction_form");

if (form) {
	form.addEventListener("submit", async (e) => {
		e.preventDefault();

		const formData = new FormData(form);
		const csrfToken = getCookie("csrftoken");

		try {
			const response = await fetch(apiTransactionUrl, {
				method: "POST",
				body: formData, // Use FormData directly
				headers: {
					"X-CSRFToken": csrfToken,
				},
			});

			if (response.ok) {
				const responseData = await response.json();
				showDynamicMessage("Transação salva...", "alert-success");
				loadTransactionData();
			} else {
				const errorData = await response.json();
				showDynamicMessage(
					`Falha ao salvar a transação: ${errorData.detail}`,
					"alert-danger",
				);
				console.log(`ERRO: ${errorData.detail}`);
			}
		} catch (error) {
			showDynamicMessage(`Error: ${error}`, "alert-danger");
		}
	});
}

function showDynamicMessage(messageText, messageClass) {
	const alertMessage = document.createElement("div");
	alertMessage.className = `alert alert-dismissible fade show ${messageClass}`;
	alertMessage.textContent = messageText;

	const container = document.querySelector(".container");
	container.insertBefore(alertMessage, container.firstChild);

	setTimeout(() => {
		alertMessage.classList.add("d-none");
	}, 5000);
}

loadTransactionData();
