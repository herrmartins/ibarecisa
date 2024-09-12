// navigation.js

import { getTransactions } from "./get_transactions.js";

let yearMonthMap = {}; // Populated from backend data

// Function to update the state of navigation buttons
function updateButtonStates(year, month) {
    const availableMonths = yearMonthMap[year] || [];
    const minMonth = Math.min(...availableMonths);
    const maxMonth = Math.max(...availableMonths);

    const firstYear = Math.min(...Object.keys(yearMonthMap).map(Number));
    const lastYear = Math.max(...Object.keys(yearMonthMap).map(Number));

    const prevButton = document.getElementById("prevButton");
    const nextButton = document.getElementById("nextButton");

    // Disable/enable previous button
    if (year === firstYear && month === minMonth) {
        prevButton.classList.remove("btn-light");
        prevButton.classList.add("btn-secondary");
        prevButton.disabled = true;
    } else {
        prevButton.classList.remove("btn-secondary");
        prevButton.classList.add("btn-light");
        prevButton.disabled = false;
    }

    // Disable/enable next button
    if (year === lastYear && month === maxMonth) {
        nextButton.classList.remove("btn-light");
        nextButton.classList.add("btn-secondary");
        nextButton.disabled = true;
    } else {
        nextButton.classList.remove("btn-secondary");
        nextButton.classList.add("btn-light");
        nextButton.disabled = false;
    }
}

// Function to update the selected month and year
function updateMonthYear(direction) {
    const yearSelect = document.getElementById("yearSelect");
    const monthSelect = document.getElementById("monthSelect");

    let year = Number.parseInt(yearSelect.value);
    let month = Number.parseInt(monthSelect.value);

    console.log(`Navigating ${direction}: Year=${year}, Month=${month}`); // Debug log

    const availableMonths = yearMonthMap[year] || [];

    if (direction === "prev") {
        if (month === Math.min(...availableMonths)) {
            year -= 1;
            if (yearMonthMap[year]) {
                const prevAvailableMonths = yearMonthMap[year];
                month = Math.max(...prevAvailableMonths);
            } else {
                year += 1; // Prevent going beyond the first year
            }
        } else {
            month -= 1;
        }
    } else if (direction === "next") {
        if (month === Math.max(...availableMonths)) {
            year += 1;
            if (yearMonthMap[year]) {
                const nextAvailableMonths = yearMonthMap[year];
                month = Math.min(...nextAvailableMonths);
            } else {
                year -= 1; // Prevent going beyond the last year
            }
        } else {
            month += 1;
        }
    }

    console.log(`Updated: Year=${year}, Month=${month}`); // Log updated values

    yearSelect.value = year;
    monthSelect.value = month;

    // Fetch transactions for the selected year and month
    getTransactions(year, month);
    updateButtonStates(year, month);
}

// Function to populate the year and month dropdowns
function populateDropdowns() {
    const yearSelect = document.getElementById("yearSelect");
    const monthSelect = document.getElementById("monthSelect");

    yearSelect.innerHTML = ""; // Clear current options
    monthSelect.innerHTML = ""; // Clear current options

    // Populate year options from yearMonthMap
    Object.keys(yearMonthMap).forEach((year) => {
        const option = document.createElement("option");
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    });

    // Set initial year and month
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;
    yearSelect.value = currentYear;
    populateMonthsForYear(currentYear);

    updateButtonStates(currentYear, currentMonth);
}

// Function to populate the month dropdown based on the selected year
function populateMonthsForYear(year) {
    const monthSelect = document.getElementById("monthSelect");
    monthSelect.innerHTML = ""; // Clear existing options

    const months = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];
    const availableMonths = yearMonthMap[year] || [];

    availableMonths.forEach((monthIndex) => {
        const option = document.createElement("option");
        option.value = monthIndex;
        option.textContent = months[monthIndex - 1];
        monthSelect.appendChild(option);
    });
    monthSelect.selectedIndex = monthSelect.options.length - 1;
}

document.addEventListener("DOMContentLoaded", async () => {
    const prevButton = document.getElementById("prevButton");
    const nextButton = document.getElementById("nextButton");
    const yearSelect = document.getElementById("yearSelect");
    const monthSelect = document.getElementById("monthSelect");

    try {
        const response = await fetch("/treasury/get-balances/");
        const data = await response.json();

        yearMonthMap = data.year_month_map;

        populateDropdowns();

        prevButton.addEventListener("click", () => {
            updateMonthYear("prev");
        });

        nextButton.addEventListener("click", () => {
            updateMonthYear("next");
        });

        yearSelect.addEventListener("change", () => {
            const selectedYear = Number.parseInt(yearSelect.value);
            populateMonthsForYear(selectedYear);
            updateButtonStates(selectedYear, Number.parseInt(monthSelect.value));
            getTransactions(selectedYear, Number.parseInt(monthSelect.value));
        });

        monthSelect.addEventListener("change", () => {
            const selectedYear = Number.parseInt(yearSelect.value);
            const selectedMonth = Number.parseInt(monthSelect.value);
            updateButtonStates(selectedYear, selectedMonth);
            getTransactions(selectedYear, selectedMonth);
        });
    } catch (error) {
        console.error("Error fetching year/month map:", error);
    }
});
