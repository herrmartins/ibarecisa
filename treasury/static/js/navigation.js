import { getTransactions } from './get_transactions.js';

document.addEventListener('DOMContentLoaded', () => {
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');

    function updateMonthYear(direction) {
        let year = Number.parseInt(yearSelect.value);
        let month = Number.parseInt(monthSelect.value);

        if (direction === 'prev') {
            if (month === 1) {
                month = 12;
                year -= 1;
            } else {
                month -= 1;
            }
        } else if (direction === 'next') {
            if (month === 12) {
                month = 1;
                year += 1;
            } else {
                month += 1;
            }
        }

        yearSelect.value = year;
        monthSelect.value = month;
        getTransactions(year, month);
    }

    prevButton.addEventListener('click', () => {
        updateMonthYear('prev');
    });

    nextButton.addEventListener('click', () => {
        updateMonthYear('next');
    });
});
