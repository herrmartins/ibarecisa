import { getTransactions } from "./get_transactions.js";

document.addEventListener("DOMContentLoaded", () => {
	const prevButton = document.getElementById("prevButton");
	const nextButton = document.getElementById("nextButton");
	const yearSelect = document.getElementById("yearSelect");
	const monthSelect = document.getElementById("monthSelect");

	let yearMonthMap = {}; // This should be populated with the data from the backend

	function updateMonthYear(direction) {
		let year = Number.parseInt(yearSelect.value);
		let month = Number.parseInt(monthSelect.value);

		const availableMonths = yearMonthMap[year] || [];

		if (direction === "prev") {
			if (month === 1) {
				year -= 1;
				if (yearMonthMap[year]) {
					month = 12;
				} else {
					year += 1;
				}
			} else {
				month -= 1;
			}
		} else if (direction === "next") {
			if (month === 12) {
				year += 1;
				if (yearMonthMap[year]) {
					month = 1;
				} else {
					year -= 1;
				}
			} else {
				month += 1;
			}
		}

		yearSelect.value = year;
		monthSelect.value = month;
		getTransactions(year, month);

		updateButtonStates(year, month);
	}

	function updateButtonStates(year, month) {
		const availableMonths = yearMonthMap[year] || [];
		const minMonth = Math.min(...availableMonths);
		const maxMonth = Math.max(...availableMonths);

		const firstYear = Math.min(...Object.keys(yearMonthMap).map(Number));
		const lastYear = Math.max(...Object.keys(yearMonthMap).map(Number));

		// Update the previous button state
		if (year === firstYear && month === minMonth) {
			prevButton.classList.remove("btn-light");
			prevButton.classList.add("btn-secondary");
			prevButton.disabled = true;
		} else {
			prevButton.classList.remove("btn-secondary");
			prevButton.classList.add("btn-light");
			prevButton.disabled = false;
		}

		// Update the next button state
		if (year === lastYear && month === maxMonth) {
			console.log("Aqui no menor");
			nextButton.classList.remove("btn-light");
			nextButton.classList.add("btn-secondary");
			nextButton.disabled = true;
		} else {
			console.log("Aqui no maior");
			nextButton.classList.remove("btn-secondary");
			nextButton.classList.add("btn-light");
			nextButton.disabled = false;
		}
	}

	prevButton.addEventListener("click", () => {
		updateMonthYear("prev");
	});

	nextButton.addEventListener("click", () => {
		updateMonthYear("next");
	});
	yearSelect.addEventListener("change", () => {
		updateButtonStates(
			Number.parseInt(yearSelect.value),
			Number.parseInt(monthSelect.value),
		);
		getTransactions(
			Number.parseInt(yearSelect.value),
			Number.parseInt(monthSelect.value),
		);
	});

	monthSelect.addEventListener("change", () => {
		updateButtonStates(
			Number.parseInt(yearSelect.value),
			Number.parseInt(monthSelect.value),
		);
		getTransactions(
			Number.parseInt(yearSelect.value),
			Number.parseInt(monthSelect.value),
		);
	});
	const initialYear = Number.parseInt(yearSelect.value);
	const initialMonth = Number.parseInt(monthSelect.value);
	updateButtonStates(initialYear, initialMonth);
    getTransactions(initialYear, initialMonth);
});
