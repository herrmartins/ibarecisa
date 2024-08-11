import { getTransactions } from './get_transactions.js';

document.addEventListener('DOMContentLoaded', () => {
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');

    function getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }

    const month = getQueryParam('month');
    const year = getQueryParam('year');

    if (month && year) {
        getTransactions(year, month);
    } else {
        const today = new Date();
        const currentYear = today.getFullYear();
        const currentMonth = today.getMonth() + 1;
        
        yearSelect.value = currentYear;
        monthSelect.value = currentMonth;
        getTransactions(currentYear, currentMonth);
    }
});
