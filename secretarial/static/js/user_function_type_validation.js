// user_validation.js

function validateUserType(userType) {
    let isPastorField = document.getElementById("id_is_pastor");
    let isSecretaryField = document.getElementById("id_is_secretary");
    let isTreasurerField = document.getElementById("id_is_treasurer");

    if (userType === "EQUIPE" || userType === "CONTRATADO") {

        isPastorField.disabled = false;
        isSecretaryField.disabled = false;
        isTreasurerField.disabled = false;
    } else {
        isPastorField.disabled = true;
        isSecretaryField.disabled = true;
        isTreasurerField.disabled = true;

        isPastorField.checked = false;
        isSecretaryField.checked = false;
        isTreasurerField.checked = false;
    }
}

function handleUserTypeChange() {
    let userTypeSelect = document.getElementById("id_type");

    if (userTypeSelect) {
        userTypeSelect.addEventListener("change", function() {
            let selectedUserType = userTypeSelect.value;
            validateUserType(selectedUserType);
        });
    }
}