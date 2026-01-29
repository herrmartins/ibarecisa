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
		// Check if clicked element or its parent has the blog-comment-toggle class
		const toggleBtn = event.target.closest(".blog-comment-toggle");
		if (toggleBtn) {
			const postId = toggleBtn.getAttribute("data-post-id");
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
	fetch(`/api2/comments/${postId}/`)
		.then((response) => response.json())
		.then((comments) => {
			if (comments.length > 0) {
				const commentTree = buildCommentTree(comments);
				const commentElements = renderCommentTree(commentTree);
				// Insert inside a reliable wrapper to avoid stray text nodes or margin-collapsing issues
				commentsContainer.innerHTML = '';
				const wrapper = document.createElement('div');
				wrapper.className = 'comment-list-wrapper';
				wrapper.innerHTML = commentElements;
				commentsContainer.appendChild(wrapper);
				commentsContainer.classList.remove('hidden');

				const authorIds = Array.from(document.querySelectorAll('.comment-item')).map(e => e.getAttribute('data-author-id'));
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
			// Handle error silently but log for diagnostics
			console.error('[comment_fetch] Erro ao carregar comentários:', error);
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
		const replyButton = `<button class="blog-reply-btn" data-comment-id="${comment.id}">
			<svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/></svg>
			Responder
		</button>`;
		const editButton = isCurrentUserAuthor(comment) ? `<button class="blog-edit-comment-btn" data-comment-id="${comment.id}">
			<svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2h2.828l8.586-8.586z"/></svg>
			Editar
		</button>` : '';
		const deleteButton = isCurrentUserAuthor(comment) ? `<button class="blog-delete-comment-btn" data-comment-id="${comment.id}" title="Excluir este comentário">
			<svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
			Excluir
		</button>` : '';
		const repliesHtml = comment.replies.length > 0 ? renderCommentTree(comment.replies, depth + 1) : '';

		return `
			<div class="comment-item ${indentClass} ${spacingClass}" data-comment-id="${comment.id}" data-author-id="${comment.author_id}">
				<div class="blog-comment-item-card">
					<div class="blog-comment-item-body">
						<div class="comment-content mb-3">${comment.content}</div>
						<div class="flex justify-between items-center">
							<div class="flex flex-row items-center gap-3">
								${comment.user_photo ? `<img src="${comment.user_photo}" alt="avatar" width="32" height="32" class="w-8 h-8 rounded-full" />` : '<div class="w-8 h-8 rounded-full bg-primary-500 text-white flex items-center justify-center"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></div>'}
								<div>
									<p class="text-sm font-semibold text-slate-800">${comment.author_name}</p>
									<p class="text-sm text-slate-500">${comment.created || 'Agora'}</p>
								</div>
							</div>
							<div class="flex flex-row items-center gap-2">
								${editButton}
								${deleteButton}
								${replyButton}
								<button class="blog-like-comment-btn" data-comment-id="${comment.id}">
									<svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"/></svg>
									<span class="like-count">${comment.likes_count || 0}</span>
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
