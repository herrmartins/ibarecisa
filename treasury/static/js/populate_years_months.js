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

            const currentYear = new Date().getFullYear();
            const currentMonth = new Date().getMonth() + 1;

            // Populate year options
            data.year_list.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                if (year == currentYear) {
                    option.selected = true;
                }
                yearSelect.appendChild(option);
            });

            // Populate months for the selected year
            function populateMonthsForYear(selectedYear) {
                monthSelect.innerHTML = '';  // Clear existing options
                const months = [
                    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
                ];

                // Check if the selected year has associated months
                if (data.year_month_map[selectedYear]) {
                    const availableMonths = data.year_month_map[selectedYear];

                    availableMonths.forEach(monthIndex => {
                        const option = document.createElement('option');
                        option.value = monthIndex;
                        option.textContent = months[monthIndex - 1];  // Adjust for 0-based index
                        if (monthIndex == currentMonth && selectedYear == currentYear) {
                            option.selected = true;
                        }
                        monthSelect.appendChild(option);
                    });
                }
            }

            // Populate months for the initially selected year
            populateMonthsForYear(yearSelect.value);

            // Handle year change
            yearSelect.addEventListener('change', (event) => {
                populateMonthsForYear(event.target.value);
            });

        } catch (error) {
            console.error('Ocorreu um erro ao receber os anos e meses:', error);
            alert(`Ocorreu um erro ao receber os anos e meses: ${error.message}`);
        }
    }

    populateDropdowns();
});
