console.log("LOCK AND LOADED")
document.addEventListener("DOMContentLoaded", () => {
	// Get the form element
	const form = document.getElementById("event-form");

	// Add a submit event listener to the form
	form.addEventListener("submit", (event) => {
		// Get the start date and end date input elements
		const startDateInput = document.getElementById("id_start_date");
		const endDateInput = document.getElementById("id_end_date");

		// Parse the input values as Date objects
		const startDate = new Date(startDateInput.value);
		const endDate = new Date(endDateInput.value);

		// Get the current date and time
		const currentDate = new Date();

		// Check if the start date is in the past
		if (startDate < currentDate) {
			alert("A data de início não pode ser passada...");
			event.preventDefault(); // Prevent form submission
		}

		// Check if the end date is after the start date
		if (endDate && endDate <= startDate) {
			alert("A data do fim não pode ser anterior a de início...");
			event.preventDefault(); // Prevent form submission
		}
	});
});
