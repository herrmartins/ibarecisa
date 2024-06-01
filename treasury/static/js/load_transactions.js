import { getTransactions } from './get_transactions.js';

document.addEventListener('DOMContentLoaded', () => {
    function getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }

    const month = getQueryParam('month');
    const year = getQueryParam('year');


    if (month && year) {
        getTransactions(month, year);
    } else {
        const today = new Date();
        getTransactions(today.getMonth() + 1, today.getFullYear());
        console.log("DADOS:", today.getFullYear(), today.getMonth())
    }
});
