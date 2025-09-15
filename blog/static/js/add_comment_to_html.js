
export function addCommentToHTML(comment) {
    const commentCard = document.createElement('div');
    commentCard.className = 'card ml-2 my-3 p-3 card-no-border shadow-sm';
    commentCard.setAttribute('data-comment-id', comment.id);

    const replyButton = `<button class="btn btn-sm btn-outline-primary reply-btn me-2" data-comment-id="${comment.id}"><i class="bi bi-reply me-1"></i>Responder</button>`;
    commentCard.innerHTML = `
        <div class="card-body p-0">
            <p class="card-text mb-3">${comment.content}</p>
            <div class="d-flex justify-content-between align-items-center">
                <div class="d-flex flex-row align-items-center">
                    ${
                        comment.user_photo
                            ? `<img src="${comment.user_photo}" alt="avatar" width="32" height="32" class="me-2" />`
                            : '<div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-2" style="width: 32px; height: 32px;"><i class="bi bi-person"></i></div>'
                    }
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
        </div>`;

    const commentsContainer = document.getElementById(`comments-${comment.post}`);
    if (commentsContainer) {
        commentsContainer.appendChild(commentCard);
        commentsContainer.classList.remove('hidden');
    }
}
