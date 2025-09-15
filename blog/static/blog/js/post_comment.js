import { getCookie } from "./get_cookie.js";
import { addCommentToHTML } from "./add_comment_to_html.js";

document
	.getElementById("posts-container")
	.addEventListener("click", (event) => {
		if (
			event.target.tagName === "BUTTON" &&
			event.target.hasAttribute("data-post-id")
		) {
			const authorId = document
				.getElementById("user-info")
				.getAttribute("comment-author-id");
			const postId = event.target.getAttribute("data-post-id");
			const commentContent = document.getElementById(`comment-${postId}`);
			postComment(authorId, postId, commentContent.value);
			commentContent.value = "";
		} else if (
			event.target.classList.contains("reply-btn")
		) {
			const commentId = event.target.getAttribute("data-comment-id");
			toggleReplyForm(commentId);
		} else if (
			event.target.classList.contains("submit-reply")
		) {
			const commentId = event.target.getAttribute("data-comment-id");
			const authorId = document
				.getElementById("user-info")
				.getAttribute("comment-author-id");
			const postId = event.target.getAttribute("data-post-id");
			const replyContent = document.getElementById(`reply-${commentId}`).value;
			postReply(authorId, postId, commentId, replyContent);
			document.getElementById(`reply-${commentId}`).value = "";
		}
	});

function postComment(authorId, postId, commentContent) {
	if (typeof postId === "undefined") {
		console.error("postId is undefined");
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
			author: authorId,
			content: commentContent,
			post: postId,
		}),
	})
		.then((response) =>
			response.ok ? response.json() : Promise.reject(response),
		)
		.then((data) => {
			console.log("Comment posted:", data);
			addCommentToHTML(data);
		})
		.catch((error) => {
			console.error("Error posting comment:", error);
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
		replyForm.className = 'reply-form mt-2';
		const postId = commentCard.closest('[id^="comments-"]').id.split('-')[1];
		replyForm.innerHTML = `
			<div class="d-flex">
				<textarea class="form-control" id="reply-${commentId}" rows="2" placeholder="Sua resposta..."></textarea>
				<button class="btn btn-primary ms-2 submit-reply" data-comment-id="${commentId}" data-post-id="${postId}">Enviar</button>
			</div>
		`;
		commentCard.appendChild(replyForm);
	}
}

function postReply(authorId, postId, parentId, content) {
	const csrftoken = getCookie("csrftoken");
	fetch(`/api2/comments/add/${postId}`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"X-CSRFToken": csrftoken,
		},
		body: JSON.stringify({
			author: authorId,
			content: content,
			post: postId,
			parent: parentId,
		}),
	})
		.then((response) =>
			response.ok ? response.json() : Promise.reject(response),
		)
		.then((data) => {
			console.log("Reply posted:", data);
			// Add the reply to the DOM
			addReplyToDOM(data, parentId);
			// Hide the reply form
			toggleReplyForm(parentId);
		})
		.catch((error) => {
			console.error("Error posting reply:", error);
		});
}

function addReplyToDOM(reply, parentId) {
	const parentCard = document.querySelector(`[data-comment-id="${parentId}"]`);
	const replyCard = document.createElement('div');
	replyCard.className = 'card ml-3 my-2 p-2 card-no-border';
	replyCard.setAttribute('data-comment-id', reply.id);
	const replyButton = `<button class="btn btn-sm btn-outline-primary reply-btn" data-comment-id="${reply.id}">Responder</button>`;
	replyCard.innerHTML = `
		<div class="card-body">
			<p class="card-text">${reply.content}</p>
			<div class="d-flex justify-content-between">
				<div class="d-flex flex-row align-items-center">
					${reply.user_photo ? `<img src="${reply.user_photo}" alt="avatar" width="25" height="25" />` : ''}
					<p class="small mb-0 ms-2">${reply.author_name}</p>
				</div>
				<div class="d-flex flex-row align-items-center">
					${replyButton}
					<p class="small text-muted mb-0 ms-2">Like</p>
					<i class="bi bi-hand-thumbs-up" style="margin-top: -0.16rem;"></i>
				</div>
			</div>
		</div>
	`;
	parentCard.appendChild(replyCard);
}
