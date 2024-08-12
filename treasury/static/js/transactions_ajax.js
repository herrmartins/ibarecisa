document.addEventListener("DOMContentLoaded", () => {
	const form = document.getElementById("transactionForm");

	form.addEventListener("submit", async (event) => {
		event.preventDefault();

		const formData = new FormData(form);
		const csrfToken = document.querySelector(
			"[name=csrfmiddlewaretoken]",
		).value;

		try {
			const response = await fetch("/treasury/add-transaction", {
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

			if (result.success) {
				const month = result.month;
				const year = result.year;
				const fetchResponse = await fetch(
					`/treasury/transactionsl/?month=${month}&year=${year}`,
					{
						headers: {
							"X-Requested-With": "XMLHttpRequest",
						},
					},
				);
				const fetchResult = await fetchResponse.json();

				document.getElementById("transactionsTable").innerHTML =
					fetchResult.html;

				// Update the current month and year in the header
				const currentMonthYearElement =
					document.getElementById("currentMonthYear");
				if (currentMonthYearElement) {
					currentMonthYearElement.textContent = `${month} ${year}`;
				}

				// Update the links for the previous and next months
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
			} else {
				console.error("Error adding transaction:", result.errors);
				alert(`Error adding transaction: ${JSON.stringify(result.errors)}`);
			}
		} catch (error) {
			console.error("An error occurred:", error);
			alert("An error occurred. Please try again.");
		}
	});
});
