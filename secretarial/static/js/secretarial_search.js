import { getCookie } from "./get_cookie.js";

const categoryDisplayNames = {
	minutes: "Atas",
	templates: "Modelos de Atas",
	users: "Usuários",
	members: "Membros",
	projects: "Projetos de Ata",
};

const searchForm = document.getElementById("search-form");
searchForm.addEventListener("submit", (event) => {
		event.preventDefault();

		const searchCriterion = document.getElementById("searched").value;
		const searchCategory = document.querySelector("select").value;
		const apiUrl = "/api/search";
		const fieldsToDisplay = [];

		fetch(apiUrl, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": getCookie("csrftoken"),
			},
			body: JSON.stringify({
				category: searchCategory,
				searched: searchCriterion,
			}),
		})
			.then((response) => {
				if (!response.ok) {
					throw new Error("Erro na resposta de requisição...");
				}
				return response.json();
			})
			.then((data) => {
				const resultsContainer = document.getElementById("search-results");
				resultsContainer.innerHTML = "";

				const container = document.createElement("div");
				container.classList.add("container");

				const row = document.createElement("div");
				row.classList.add("row", "justify-content-center");

				const col = document.createElement("div");
				col.classList.add("col-10");

				const card = document.createElement("div");
				card.classList.add("card", "my-4");

				const cardBody = document.createElement("div");
				cardBody.classList.add("card-body");

				const categoryDisplayName =
					categoryDisplayNames[searchCategory] || searchCategory;

				const categoryHeader = document.createElement("p");
				categoryHeader.classList.add("fs-5", "fw-bold", "mb-3", "d-block");
				categoryHeader.textContent = `Categoria: ${categoryDisplayName}`;

				cardBody.appendChild(categoryHeader);
				cardBody.appendChild(document.createElement("hr"));

				if (data.length === 0) {
					const noResultsMessage = document.createElement("p");
					noResultsMessage.textContent =
						"Não há resultados para este critério de busca.";
					cardBody.appendChild(noResultsMessage);
				} else {
					const resultList = document.createElement("ul");
					resultList.classList.add("list-group");

					data.forEach((item) => {
						let displayFields = "";
						const listItem = document.createElement("li");
						listItem.classList.add("list-group-item");

						if (searchCategory === "minutes") {
							displayFields = `Presidente: ${item.president} | Data: ${item.meeting_date}`;

							const link = document.createElement("a");
							link.textContent = "Ver Ata";
							link.href = `/secretarial/meeting/detail/${item.id}`;

							listItem.appendChild(
								document.createTextNode(displayFields + " "),
							);
							listItem.appendChild(link);
						} else if (searchCategory === "templates") {
							displayFields = item.title;
							listItem.appendChild(document.createTextNode(displayFields));
						} else if (searchCategory === "projects") {
							displayFields = `Presidente: ${item.president} | Data: ${item.meeting_date}`;

							const link = document.createElement("a");
							link.textContent = "Ver Projeto";
							link.href = `/secretarial/meeting/projects/edit/${item.id}/`;

							listItem.appendChild(
								document.createTextNode(displayFields + " "),
							);
							listItem.appendChild(link);
						} else if (
							searchCategory === "users" ||
							searchCategory === "members"
						) {
							displayFields = `${item.first_name} ${item.last_name}`;
							listItem.appendChild(document.createTextNode(displayFields));
						}

						resultList.appendChild(listItem); // Append the constructed listItem to resultList
					});

					cardBody.appendChild(resultList);
				}

				card.appendChild(cardBody);
				col.appendChild(card);
				row.appendChild(col);
				container.appendChild(row);
				resultsContainer.appendChild(container);
			})
			.catch((error) => {
				console.error("Error:", error);
			});
});
