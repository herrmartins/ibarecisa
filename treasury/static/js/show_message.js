export function showDynamicMessage(messageText, messageClass) {
    const alertMessage = document.createElement("div");
    alertMessage.className = `alert alert-dismissible fade show ${messageClass}`;
    alertMessage.textContent = messageText;

    const container = document.querySelector(".container");
    container.insertBefore(alertMessage, container.firstChild);

    setTimeout(() => {
        alertMessage.classList.add("d-none");
    }, 5000);
}