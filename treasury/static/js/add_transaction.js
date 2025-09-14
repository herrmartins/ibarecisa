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
            document.getElementById('yearSelect').value = result.year;
            document.getElementById('monthSelect').value = result.month;
            getTransactions(result.year, result.month);


        } else {
            let errorMessage = "";

            if (result.errors.__all__) {
                errorMessage = result.errors.__all__;
            } else {
                const fieldErrors = [];
                for (const [field, messages] of Object.entries(result.errors)) {
                    fieldErrors.push(`${field}: ${messages.join(", ")}`);
                }
                errorMessage = fieldErrors.join("; ");
            }

            const errorDiv = document.getElementById('transactionError');
            const errorSpan = document.getElementById('errorMessage');
            errorSpan.textContent = errorMessage;
            errorDiv.style.display = 'block';

            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
    } catch (error) {
        const errorDiv = document.getElementById('transactionError');
        const errorSpan = document.getElementById('errorMessage');
        errorSpan.textContent = "Erro inesperado. Tente novamente.";
        errorDiv.style.display = 'block';

        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

function hideError() {
    const errorDiv = document.getElementById('transactionError');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('transaction_form');
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', hideError);
            input.addEventListener('change', hideError);
        });
    }
});

window.addTransaction = addTransaction;
