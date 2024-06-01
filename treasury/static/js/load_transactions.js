import { getTransactions } from './get_transactions.js';

document.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const month = today.getMonth() + 1;
    const year = today.getFullYear();
    getTransactions(month, year);
});
