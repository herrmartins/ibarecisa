// post_comment.js

document
	.getElementById("posts-container")
	.addEventListener("click", (event) => {
		// Check for submit-reply button (or its parent)
		const submitReplyBtn = event.target.closest(".submit-reply") || event.target.closest(".blog-submit-reply-btn");
		if (submitReplyBtn) {
			const commentId = submitReplyBtn.getAttribute("data-comment-id");
			const authorId = document
				.getElementById("user-info")
				.getAttribute("comment-author-id");
			const postId = submitReplyBtn.getAttribute("data-post-id");
			const replyElem = document.getElementById(`reply-${commentId}`);
			const replyContent = replyElem ? replyElem.value : "";
			postReply(authorId, postId, commentId, replyContent);
			if (replyElem) replyElem.value = "";
			return;
		}

		// Check for reply-btn button (or its parent)
		const replyBtn = event.target.closest(".blog-reply-btn");
		if (replyBtn) {
			const commentId = replyBtn.getAttribute("data-comment-id");
			toggleReplyForm(commentId);
			return;
		}

		// Check for send comment button (or its parent)
		const sendCommentBtn = event.target.closest("button[id^='sendComment-']");
		if (sendCommentBtn) {
			const authorId = document
				.getElementById("user-info")
				.getAttribute("comment-author-id");
			const postId = sendCommentBtn.getAttribute("data-post-id");
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
		replyForm.className = 'reply-form mt-3 p-3 bg-slate-50 rounded-xl border border-slate-200';
		const postId = commentCard.closest('[id^="comments-"]').id.split('-')[1];
		replyForm.innerHTML = `
			<div class="flex gap-2">
				<textarea class="blog-reply-textarea flex-grow-1" id="reply-${commentId}" rows="2" placeholder="Digite sua resposta..."></textarea>
				<button class="blog-submit-reply-btn" data-comment-id="${commentId}" data-post-id="${postId}">
					<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
					Enviar
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
			// Handle error silently
		});
}

function isCurrentUserAuthor(comment) {
    const userInfo = document.getElementById("user-info");
    if (!userInfo) return false;

    const currentUserId = userInfo.getAttribute("comment-author-id");
    return currentUserId && currentUserId !== "null" && comment.author_id == currentUserId;
}

function addReplyToDOM(reply, parentId) {
    const parentCard = document.querySelector(`[data-comment-id="${parentId}"]`);
    const replyCard = document.createElement('div');
    replyCard.className = 'blog-reply-card ml-3 my-3 p-3';
    replyCard.setAttribute('data-comment-id', reply.id);
    const replyButton = `<button class="blog-reply-btn" data-comment-id="${reply.id}" title="Responder a este comentário">
		<svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/></svg>
		Responder
	</button>`;
    const editButton = isCurrentUserAuthor(reply) ? `<button class="blog-edit-comment-btn" data-comment-id="${reply.id}">
		<svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2h2.828l8.586-8.586z"/></svg>
		Editar
	</button>` : '';
    const deleteButton = isCurrentUserAuthor(reply) ? `<button class="blog-delete-comment-btn" data-comment-id="${reply.id}" title="Excluir este comentário">
		<svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
		Excluir
	</button>` : '';
    const timeAgo = reply.created ? new Date(reply.created).toLocaleString('pt-BR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }) : 'Agora mesmo';

    replyCard.innerHTML = `
		<div class="blog-reply-body">
			<div class="flex mb-3 gap-3">
				<div class="flex-shrink-0">
					${
						reply.user_photo
							? `<img src="${reply.user_photo}" alt="avatar" width="32" height="32" class="w-8 h-8 rounded-full border-2 border-primary-300 shadow-sm" />`
							: '<div class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 text-white flex items-center justify-center border-2 border-primary-300 shadow-sm"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></div>'
					}
				</div>
				<div class="flex-grow-1">
					<div class="flex items-center mb-2 gap-2">
						<h6 class="font-bold text-primary-600 m-0">${reply.author_name}</h6>
						<span class="text-slate-500 text-sm">
							<svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
							<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">${timeAgo}</span>
						</span>
					</div>
					<p class="mb-3" style="line-height: 1.6;">${reply.content}</p>
					<div class="flex justify-between items-center">
						<div class="flex gap-2">
							${editButton}
							${deleteButton}
							${replyButton}
							<button class="blog-like-comment-btn" data-comment-id="${reply.id}" title="Curtir este comentário">
								<svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
								<span class="like-count">${reply.likes_count || 0}</span>
							</button>
						</div>
						<span class="text-slate-500 text-sm">
							<svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 16h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
							<span class="comment-thread-count">0 respostas</span>
						</span>
					</div>
				</div>
			</div>
		</div>
	`;
    parentCard.appendChild(replyCard);
}
