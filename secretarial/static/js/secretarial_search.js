// Helper function to get CSRF token
function getCookie(name) {
	let cookieValue = null;
	if (document.cookie && document.cookie !== "") {
		const cookies = document.cookie.split(";");
		for (let i = 0; i < cookies.length; i++) {
			const cookie = cookies[i].trim();
			if (cookie.startsWith(name + "=")) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

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
		const searchCategory = document.getElementById("search-type").value;
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

				// Main container with Tailwind classes
				const container = document.createElement("div");
				container.className = "w-full";

				// Results card
				const card = document.createElement("div");
				card.className = "mt-4 bg-white/95 backdrop-blur-xl border border-white/80 rounded-xl shadow-lg overflow-hidden";

				// Card header/body
				const cardBody = document.createElement("div");
				cardBody.className = "p-4";

				const categoryDisplayName =
					categoryDisplayNames[searchCategory] || searchCategory;

				const categoryHeader = document.createElement("div");
				categoryHeader.className = "text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2";
				categoryHeader.innerHTML = `
					<svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
					</svg>
					${categoryDisplayName}
				`;

				cardBody.appendChild(categoryHeader);

				// Divider
				const divider = document.createElement("div");
				divider.className = "h-px bg-slate-200 mb-4";
				cardBody.appendChild(divider);

				if (data.length === 0) {
					const noResultsMessage = document.createElement("div");
					noResultsMessage.className = "text-center py-8 text-slate-500";
					noResultsMessage.innerHTML = `
						<svg class="w-12 h-12 mx-auto mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
						</svg>
						<p>Não há resultados para este critério de busca.</p>
					`;
					cardBody.appendChild(noResultsMessage);
				} else {
					const resultList = document.createElement("div");
					resultList.className = "space-y-2";

					data.forEach((item) => {
						const resultItem = document.createElement("div");
						resultItem.className = "flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors";

						if (searchCategory === "minutes") {
							const infoText = `Presidente: ${item.president} | Data: ${item.meeting_date}`;
							const link = document.createElement("a");
							link.textContent = "Ver Ata";
							link.href = `/secretarial/meeting/detail/${item.id}`;
							link.className = "inline-flex items-center gap-1 px-3 py-1.5 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors";

							const textSpan = document.createElement("span");
							textSpan.className = "text-slate-700";
							textSpan.textContent = infoText;

							resultItem.appendChild(textSpan);
							resultItem.appendChild(link);
						} else if (searchCategory === "templates") {
							resultItem.className = "p-3 bg-slate-50 rounded-lg";
							resultItem.innerHTML = `<span class="text-slate-700 font-medium">${item.title}</span>`;
						} else if (searchCategory === "projects") {
							const infoText = `Presidente: ${item.president} | Data: ${item.meeting_date}`;
							const link = document.createElement("a");
							link.textContent = "Ver Projeto";
							link.href = `/secretarial/meeting/projects/edit/${item.id}/`;
							link.className = "inline-flex items-center gap-1 px-3 py-1.5 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors";

							const textSpan = document.createElement("span");
							textSpan.className = "text-slate-700";
							textSpan.textContent = infoText;

							resultItem.appendChild(textSpan);
							resultItem.appendChild(link);
						} else if (
							searchCategory === "users" ||
							searchCategory === "members"
						) {
							resultItem.className = "p-3 bg-slate-50 rounded-lg flex items-center gap-3";
							resultItem.innerHTML = `
								<div class="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-semibold">
									${item.first_name ? item.first_name[0].toUpperCase() : '?'}
								</div>
								<span class="text-slate-700 font-medium">${item.first_name} ${item.last_name}</span>
							`;
						}

						resultList.appendChild(resultItem);
					});

					cardBody.appendChild(resultList);
				}

				card.appendChild(cardBody);
				container.appendChild(card);
				resultsContainer.appendChild(container);
			})
			.catch((error) => {
				console.error("Error:", error);
				const resultsContainer = document.getElementById("search-results");
				resultsContainer.innerHTML = `
					<div class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
						<p class="text-red-600">Erro ao realizar busca. Tente novamente.</p>
					</div>
				`;
			});
});
