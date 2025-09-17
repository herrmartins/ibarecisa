/* getCookie and addCommentToHTML are available globally via window.getCookie and window.addCommentToHTML */

document
	.getElementById("posts-container")
	.addEventListener("click", (event) => {
		if (event.target.classList.contains("submit-reply")) {
			const commentId = event.target.getAttribute("data-comment-id");
			const authorId = document
				.getElementById("user-info")
				.getAttribute("comment-author-id");
			const postId = event.target.getAttribute("data-post-id");
			const replyElem = document.getElementById(`reply-${commentId}`);
			const replyContent = replyElem ? replyElem.value : "";
			postReply(authorId, postId, commentId, replyContent);
			if (replyElem) replyElem.value = "";
			return;
		}

		if (event.target.classList.contains("reply-btn")) {
			const commentId = event.target.getAttribute("data-comment-id");
			toggleReplyForm(commentId);
			return;
		}

		if (
			event.target.tagName === "BUTTON" &&
			event.target.hasAttribute("data-post-id") &&
			event.target.id &&
			event.target.id.startsWith("sendComment-")
		) {
			const authorId = document
				.getElementById("user-info")
				.getAttribute("comment-author-id");
			const postId = event.target.getAttribute("data-post-id");
			const commentElem = document.getElementById(`comment-${postId}`);
			if (!commentElem) {
				return;
			}
			const commentValue = commentElem.value;
			postComment(authorId, postId, commentValue);
			commentElem.value = "";
			return;
		}
	});

function postComment(authorId, postId, commentContent) {
	if (typeof postId === "undefined") {
		return;
	}

	const content = (commentContent || "").trim();
	if (!content) {
		alert("O comentário não pode ficar vazio.");
		return;
	}

	const csrftoken = getCookie("csrftoken");
	fetch(`/api2/comments/add/${postId}/`, {
		method: "POST",
		credentials: 'same-origin',
		headers: {
			"Content-Type": "application/json",
			"X-CSRFToken": csrftoken,
		},
		body: JSON.stringify({
			content: content
		}),
	})
		.then((response) =>
			response.ok ? response.json() : Promise.reject(response),
		)
		.then((data) => {
			addCommentToHTML(data);
		})
		.catch((error) => {
			console.error('[postComment] Erro ao postar comentário:', error);
			// If the rejected value is a Response, try to log its body for diagnostics
			if (error && typeof error.text === 'function') {
				error.text().then(txt => console.error('[postComment] response text:', txt)).catch(() => {});
			}
			alert('Erro ao enviar comentário. Tente novamente.');
		});
}

window.postComment = postComment;

function toggleReplyForm(commentId) {
	const commentCard = document.querySelector(`[data-comment-id="${commentId}"]`);
	let replyForm = commentCard.querySelector('.reply-form');

	if (replyForm) {
		replyForm.remove();
	} else {
		replyForm = document.createElement('div');
		replyForm.className = 'reply-form mt-3 p-3 bg-light rounded-3 border';
		const postId = commentCard.closest('[id^="comments-"]').id.split('-')[1];
		replyForm.innerHTML = `
			<div class="d-flex gap-2">
				<textarea class="form-control flex-grow-1" id="reply-${commentId}" rows="2" placeholder="Digite sua resposta..."></textarea>
				<button class="btn btn-primary px-3 submit-reply align-self-start" data-comment-id="${commentId}" data-post-id="${postId}">
					<i class="bi bi-send me-1"></i>Enviar
				</button>
			</div>
		`;
		commentCard.appendChild(replyForm);
	}
}

function postReply(authorId, postId, parentId, content) {
	const replyContent = (content || "").trim();
	if (!replyContent) {
		alert("A resposta não pode ficar vazia.");
		return;
	}

	const csrftoken = getCookie("csrftoken");
	fetch(`/api2/comments/add/${postId}/`, {
		method: "POST",
		credentials: 'same-origin',
		headers: {
			"Content-Type": "application/json",
			"X-CSRFToken": csrftoken,
		},
		body: JSON.stringify({
			content: replyContent,
			parent: parentId
		}),
	})
		.then((response) =>
			response.ok ? response.json() : Promise.reject(response),
		)
		.then((data) => {
			// Add the reply to the DOM
			addReplyToDOM(data, parentId);
			// Hide the reply form
			toggleReplyForm(parentId);
		})
		.catch((error) => {
			console.error('[postReply] Erro ao postar resposta:', error);
			if (error && typeof error.text === 'function') {
				error.text().then(txt => console.error('[postReply] response text:', txt)).catch(() => {});
			}
			alert('Erro ao enviar resposta. Tente novamente.');
		});
}

function addReplyToDOM(reply, parentId) {
	const parentCard = document.querySelector(`[data-comment-id="${parentId}"]`);
	const replyCard = document.createElement('div');
	replyCard.className = 'card ml-3 my-3 p-3 card-no-border shadow-sm';
	replyCard.setAttribute('data-comment-id', reply.id);
	const replyButton = `<button class="btn btn-sm btn-outline-primary reply-btn me-2 rounded-pill" data-comment-id="${reply.id}" data-bs-toggle="tooltip" title="Responder a este comentário"><i class="bi bi-reply me-1"></i>Responder</button>`;
	const deleteButton = `<button class="btn btn-sm btn-outline-danger delete-btn me-2 rounded-pill" data-comment-id="${reply.id}" data-bs-toggle="tooltip" title="Excluir este comentário"><i class="bi bi-trash me-1"></i>Excluir</button>`;
	const timeAgo = reply.created ? new Date(reply.created).toLocaleString('pt-BR', {
		year: 'numeric',
		month: 'short',
		day: 'numeric',
		hour: '2-digit',
		minute: '2-digit'
	}) : 'Agora mesmo';

	replyCard.innerHTML = `
		<div class="card-body p-0">
			<div class="d-flex mb-3">
				<div class="flex-shrink-0 me-3">
					${
						reply.user_photo
							? `<img src="${reply.user_photo}" alt="avatar" width="32" height="32" class="rounded-circle border border-2 border-primary shadow-sm" />`
							: '<div class="bg-gradient text-white rounded-circle d-flex align-items-center justify-content-center border border-2 border-primary shadow-sm" style="width: 32px; height: 32px;"><i class="bi bi-person-fill fs-5"></i></div>'
					}
				</div>
				<div class="flex-grow-1">
					<div class="d-flex align-items-center mb-2">
						<h6 class="card-title mb-0 fw-bold text-primary">${reply.author_name}</h6>
						<small class="text-muted ms-2">
							<i class="bi bi-clock me-1"></i>
							<span class="badge bg-light text-muted border">${timeAgo}</span>
						</small>
					</div>
					<p class="card-text mb-3 lh-base" style="line-height: 1.6;">${reply.content}</p>
					<div class="d-flex justify-content-between align-items-center">
						<div class="d-flex gap-2">
							${deleteButton}
							${replyButton}
							<button class="btn btn-sm btn-outline-success like-btn rounded-pill" data-comment-id="${reply.id}" data-bs-toggle="tooltip" title="Curtir este comentário">
								<i class="bi bi-heart me-1"></i>
								<span class="like-count">${reply.likes_count || 0}</span>
							</button>
						</div>
						<small class="text-muted">
							<i class="bi bi-chat-dots me-1"></i>
							<span class="comment-thread-count">0 respostas</span>
						</small>
					</div>
				</div>
			</div>
		</div>
	`;
	parentCard.appendChild(replyCard);

	// Initialize tooltips for the new buttons
	const tooltipTriggerList = [].slice.call(replyCard.querySelectorAll('[data-bs-toggle="tooltip"]'));
	const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
		return new bootstrap.Tooltip(tooltipTriggerEl);
	});
}
