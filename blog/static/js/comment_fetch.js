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

	// Create a map of comments by id
	comments.forEach(comment => {
		comment.replies = [];
		commentMap[comment.id] = comment;
	});

	// Build the tree
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
		const replyButton = `<button class="btn btn-sm btn-outline-primary reply-btn me-2" data-comment-id="${comment.id}"><i class="bi bi-reply me-1"></i>Responder</button>`;
		const repliesHtml = comment.replies.length > 0 ? renderCommentTree(comment.replies, depth + 1) : '';

		return `
			<div class="card ${indentClass} my-3 p-3 card-no-border shadow-sm" data-comment-id="${comment.id}">
				<div class="card-body p-0">
					<p class="card-text mb-3">${comment.content}</p>
					<div class="d-flex justify-content-between align-items-center">
						<div class="d-flex flex-row align-items-center">
							${comment.user_photo ? `<img src="${comment.user_photo}" alt="avatar" width="32" height="32" class="me-2" />` : '<div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-2" style="width: 32px; height: 32px;"><i class="bi bi-person"></i></div>'}
							<div>
								<p class="small mb-0 fw-semibold">${comment.author_name}</p>
								<p class="small text-muted mb-0">${comment.created || 'Agora'}</p>
							</div>
						</div>
						<div class="d-flex flex-row align-items-center">
							${replyButton}
							<button class="btn btn-sm btn-outline-secondary me-2 like-btn" data-comment-id="${comment.id}">
								<i class="bi bi-hand-thumbs-up me-1"></i><span class="like-count">${comment.likes_count || 0}</span>
							</button>
						</div>
					</div>
				</div>
				${repliesHtml}
			</div>
		`;
	}).join('');
}
