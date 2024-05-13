function deleteTransaction() {
    if (confirm('Confirma que queres deletar esta transação?')) {
        const form = document.getElementById('deleteForm');
        form.submit();
    }
}