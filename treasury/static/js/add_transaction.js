import { getTransactions } from './get_transactions.js';

async function addTransaction(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
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
            throw new Error(`Formato da resposta não é JSON: ${errorText}`);
        }

        const result = await response.json();

        if (result.success) {
            getTransactions(result.year, result.month);
            document.getElementById('yearSelect').value = result.year;
            document.getElementById('monthSelect').value = result.month;


        } else {
            console.error("Erro ao adicionar a transação:", result.errors);
            alert(`Error adding transaction: ${JSON.stringify(result.errors)}`);
        }
    } catch (error) {
        console.error("An error occurred:", error);
        alert("An error occurred. Please try again.");
    }
}

window.addTransaction = addTransaction;
