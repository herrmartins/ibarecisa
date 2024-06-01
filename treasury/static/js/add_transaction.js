import { getTransactions } from './get_transactions.js';

async function addTransaction(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    try {
        console.log("Attempting to add transaction...");
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
            throw new Error(`Resposta não é JSON: ${errorText}`);
        }

        const result = await response.json();
        console.log("Transaction add result:", result);

        if (result.success) {
            console.log("Transaction added successfully. Fetching transactions...");
            getTransactions(result.month, result.year); // Fetch and update transactions list after adding
        } else {
            console.error("Error adding transaction:", result.errors);
            alert(`Error adding transaction: ${JSON.stringify(result.errors)}`);
        }
    } catch (error) {
        console.error("An error occurred:", error);
        alert("An error occurred. Please try again.");
    }
}

// Ensure the function is accessible globally
window.addTransaction = addTransaction;
