import { getCookie } from "./get_cookie.js";
import { addCommentToHTML } from "./add_comment_to_html.js";

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
	fetch(`/api2/comments/add/${postId}`, {
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
			// Handle error silently
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
	fetch(`/api2/comments/add/${postId}`, {
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

function addReplyToDOM(reply, parentId) {
	const parentCard = document.querySelector(`[data-comment-id="${parentId}"]`);
	const replyCard = document.createElement('div');
	replyCard.className = 'card ml-3 my-3 p-3 card-no-border shadow-sm';
	replyCard.setAttribute('data-comment-id', reply.id);
	const replyButton = `<button class="btn btn-sm btn-outline-primary reply-btn me-2" data-comment-id="${reply.id}"><i class="bi bi-reply me-1"></i>Responder</button>`;
	replyCard.innerHTML = `
		<div class="card-body p-0">
			<p class="card-text mb-3">${reply.content}</p>
			<div class="d-flex justify-content-between align-items-center">
				<div class="d-flex flex-row align-items-center">
					${reply.user_photo ? `<img src="${reply.user_photo}" alt="avatar" width="32" height="32" class="me-2" />` : '<div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-2" style="width: 32px; height: 32px;"><i class="bi bi-person"></i></div>'}
					<div>
						<p class="small mb-0 fw-semibold">${reply.author_name}</p>
						<p class="small text-muted mb-0">${reply.created || 'Agora'}</p>
					</div>
				</div>
				<div class="d-flex flex-row align-items-center">
					${replyButton}
					<button class="btn btn-sm btn-outline-secondary me-2 like-btn" data-comment-id="${reply.id}">
						<i class="bi bi-hand-thumbs-up me-1"></i><span class="like-count">${reply.likes_count || 0}</span>
					</button>
				</div>
			</div>
		</div>
	`;
	parentCard.appendChild(replyCard);
}
