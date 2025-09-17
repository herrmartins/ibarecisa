// comment_fetch.js

function isCurrentUserAuthor(comment) {
	const userInfo = document.getElementById("user-info");
	if (!userInfo) return false;

	const currentUserId = userInfo.getAttribute("comment-author-id");
	// Normalize to strings to avoid type/coercion issues and make check deterministic.
	if (!currentUserId || currentUserId === "null") return false;
	return String(comment.author_id) === String(currentUserId);
}

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

	// Debug: log current user id attribute so we can diagnose missing "Editar" buttons
	try {
		const userInfo = document.getElementById("user-info");
	} catch (e) {
		console.debug('[comment_fetch] unable to read user-info', e);
	}

	// Always fetch fresh comments from the API when opening the comments pane.
	// This ensures the client-side renderer (which adds Edit buttons for the current user)
	// is used even if the server injected HTML is present.
	fetch(`/api2/comments/${postId}`)
		.then((response) => response.json())
		.then((comments) => {
			if (comments.length > 0) {
				const commentTree = buildCommentTree(comments);
				const commentElements = renderCommentTree(commentTree);
				commentsContainer.innerHTML = commentElements;
			} else {
				commentsContainer.innerHTML = '';
				const noCommentsMsg = document.createElement("p");
				noCommentsMsg.textContent = "Seja o primeiro a comentar...";
				commentsContainer.appendChild(noCommentsMsg);
				setTimeout(() => {
					noCommentsMsg.style.display = "none";
				}, 3000);
			}
		})
		.catch((error) => {
			// Handle error silently
			console.error('Erro ao carregar comentários:', error);
		});
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
		const spacingClass = depth > 0 ? 'my-3' : 'mb-3';
		const replyButton = `<button class="btn btn-sm btn-outline-primary reply-btn me-2" data-comment-id="${comment.id}"><i class="bi bi-reply me-1"></i>Responder</button>`;
		const editButton = isCurrentUserAuthor(comment) ? `<button class="btn btn-sm btn-outline-warning edit-btn me-2" data-comment-id="${comment.id}"><i class="bi bi-pencil me-1"></i>Editar</button>` : '';
		const repliesHtml = comment.replies.length > 0 ? renderCommentTree(comment.replies, depth + 1) : '';

		return `
			<div class="comment-item ${indentClass} ${spacingClass}" data-comment-id="${comment.id}" data-author-id="${comment.author_id}">
				<div class="card p-3 card-no-border shadow-sm">
					<div class="card-body p-0">
						<div class="comment-content mb-3">${comment.content}</div>
						<div class="d-flex justify-content-between align-items-center">
							<div class="d-flex flex-row align-items-center">
								${comment.user_photo ? `<img src="${comment.user_photo}" alt="avatar" width="32" height="32" class="me-2" />` : '<div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-2" style="width: 32px; height: 32px;"><i class="bi bi-person"></i></div>'}
								<div>
									<p class="small mb-0 fw-semibold">${comment.author_name}</p>
									<p class="small text-muted mb-0">${comment.created || 'Agora'}</p>
								</div>
							</div>
							<div class="d-flex flex-row align-items-center">
								${editButton}
								${replyButton}
								<button class="btn btn-sm btn-outline-secondary me-2 like-btn" data-comment-id="${comment.id}">
									<i class="bi bi-hand-thumbs-up me-1"></i><span class="like-count">${comment.likes_count || 0}</span>
								</button>
							</div>
						</div>
					</div>
				</div>
				<div class="replies">
					${repliesHtml}
				</div>
			</div>
		`;
	}).join('');
}
