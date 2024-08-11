document.addEventListener('DOMContentLoaded', () => {
    async function populateDropdowns() {
        try {
            const response = await fetch('/treasury/get-balances/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                throw new Error(`Erro... Resposta da rede: ${response.statusText}`);
            }

            const data = await response.json();
            const yearSelect = document.getElementById('yearSelect');
            const monthSelect = document.getElementById('monthSelect');

            // Clear existing options
            yearSelect.innerHTML = '';
            monthSelect.innerHTML = '';

            // Get the current year
            const currentYear = new Date().getFullYear();

            // Populate year options
            // biome-ignore lint/complexity/noForEach: <explanation>
                        data.year_list.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                if (year === currentYear) {
                    option.selected = true;
                }
                yearSelect.appendChild(option);
            });

            // Populate month options
            const months = [
                'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
            ];
            months.forEach((month, index) => {
                const option = document.createElement('option');
                option.value = index + 1;
                option.textContent = month;
                monthSelect.appendChild(option);
            });

            // Set the current month as the default selection
            const currentMonth = new Date().getMonth() + 1;
            monthSelect.value = currentMonth;

        } catch (error) {
            console.error('Ocorreu um erro ao receber os anos e meses:', error);
            alert('Ocorreu um erro ao receber os anos e meses. Tente novamente...');
        }
    }

    populateDropdowns();
});
