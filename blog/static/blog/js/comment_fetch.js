import { getCookie } from "./get_cookie.js";

document
	.getElementById("posts-container")
	.addEventListener("click", (event) => {
		if (event.target.classList.contains("bi-chat-left-dots")) {
			const postId = event.target.getAttribute("data-post-id");
			loadComments(postId);
		}
	});

function loadComments(postId) {
	const commentsContainer = document.getElementById(`comments-${postId}`);
	const form = document.getElementById(`form-${postId}`);
	if (!commentsContainer.classList.contains("hidden")) {
		commentsContainer.classList.add("hidden");
		form.classList.add("hidden");
	} else {
		commentsContainer.classList.remove("hidden");
		form.classList.remove("hidden");
	}

	if (commentsContainer.innerHTML.trim() === "") {
		fetch(`/api2/comments/${postId}`)
			.then((response) => response.json())
			.then((comments) => {
				console.log("Comentários", comments);
				if (comments.length > 0) {
					const commentTree = buildCommentTree(comments);
					const commentElements = renderCommentTree(commentTree);
					commentsContainer.innerHTML = commentElements;
				} else {
					const noCommentsMsg = document.createElement("p");
					noCommentsMsg.textContent = "Seja o primeiro a comentar...";
					commentsContainer.appendChild(noCommentsMsg);
					setTimeout(() => {
						noCommentsMsg.style.display = "none";
					}, 3000);
				}
			})
			.catch((error) => {
				console.error("Error fetching comments:", error);
			});
	}
}

function buildCommentTree(comments) {
	const commentMap = {};
	const roots = [];

	comments.forEach(comment => {
		comment.replies = [];
		commentMap[comment.id] = comment;
	});

	comments.forEach(comment => {
		if (comment.parent) {
			if (commentMap[comment.parent]) {
				commentMap[comment.parent].replies.push(comment);
			}
		} else {
			roots.push(comment);
		}
	});

	return roots;
}

function renderCommentTree(comments, depth = 0) {
	return comments.map(comment => {
		const indentClass = depth > 0 ? `ml-${depth * 3}` : '';
		const replyButton = `<button class="btn btn-sm btn-outline-primary reply-btn" data-comment-id="${comment.id}">Responder</button>`;
		const repliesHtml = comment.replies.length > 0 ? renderCommentTree(comment.replies, depth + 1) : '';

		return `
			<div class="card ${indentClass} my-2 p-2 card-no-border" data-comment-id="${comment.id}">
				<div class="card-body">
					<p class="card-text">${comment.content}</p>
					<div class="d-flex justify-content-between">
						<div class="d-flex flex-row align-items-center">
							${comment.user_photo ? `<img src="${comment.user_photo}" alt="avatar" width="25" height="25" />` : ''}
							<p class="small mb-0 ms-2">${comment.author_name}</p>
						</div>
						<div class="d-flex flex-row align-items-center">
							${replyButton}
							<p class="small text-muted mb-0 ms-2">Like</p>
							<i class="bi bi-hand-thumbs-up" style="margin-top: -0.16rem;"></i>
						</div>
					</div>
				</div>
				${repliesHtml}
			</div>
		`;
	}).join('');
}
