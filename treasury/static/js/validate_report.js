function calculateSum() {
	const inCash = Number.parseFloat(document.getElementById("id_in_cash").value) || 0;
	const inCurrentAccount =
		Number.parseFloat(document.getElementById("id_in_current_account").value) || 0;
	const inSavingsAccount =
		Number.parseFloat(document.getElementById("id_in_savings_account").value) || 0;
	const totalBalance =
		Number.parseFloat(document.getElementById("id_total_balance").value) || 0;
	const responseField = document.getElementById("field_status");

	const total = inCash + inCurrentAccount + inSavingsAccount;

	const submitBtn = document.getElementById("submitBtn");
	if (total !== 0 && total !== totalBalance) {
		responseField.innerText =
			"A soma dos campos não bate com o valor do saldo final ou é diferente de 0...";
		submitBtn.disabled = true;
	} else {
		responseField.innerText = "";
		submitBtn.disabled = false;
	}
}

document.addEventListener("DOMContentLoaded", () => {
	calculateSum();
});

const inputFields = document.querySelectorAll(
	"#id_in_cash, #id_in_current_account, #id_in_savings_account",
);
// biome-ignore lint/complexity/noForEach: <explanation>
inputFields.forEach((field) => {
	field.addEventListener("input", calculateSum);
});
