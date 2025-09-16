
function addCommentToHTML(comment) {
    const commentCard = document.createElement('div');
    commentCard.className = 'card my-3 p-4 card-no-border shadow-sm animate__animated animate__fadeInUp';
    commentCard.setAttribute('data-comment-id', comment.id);
    commentCard.style.animationDelay = '0.1s';
 
    const replyButton = `<button class="btn btn-sm btn-outline-primary reply-btn me-2 rounded-pill" data-comment-id="${comment.id}" data-bs-toggle="tooltip" title="Responder a este comentário"><i class="bi bi-reply-fill me-1"></i>Responder</button>`;
    const timeAgo = comment.created ? new Date(comment.created).toLocaleString('pt-BR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }) : 'Agora mesmo';
 
    commentCard.innerHTML = `
        <div class="card-body p-0">
            <div class="d-flex mb-3">
                <div class="flex-shrink-0 me-3">
                    ${
                        comment.user_photo
                            ? `<img src="${comment.user_photo}" alt="avatar" width="40" height="40" class="rounded-circle border border-2 border-primary shadow-sm" />`
                            : '<div class="bg-gradient text-white rounded-circle d-flex align-items-center justify-content-center border border-2 border-primary shadow-sm" style="width: 40px; height: 40px;"><i class="bi bi-person-fill fs-5"></i></div>'
                    }
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-2">
                        <h6 class="card-title mb-0 fw-bold text-primary">${comment.author_name}</h6>
                        <small class="text-muted ms-2">
                            <i class="bi bi-clock me-1"></i>
                            <span class="badge bg-light text-muted border">${timeAgo}</span>
                        </small>
                    </div>
                    <p class="card-text mb-3 lh-base" style="line-height: 1.6;">${comment.content}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex gap-2">
                            ${replyButton}
                            <button class="btn btn-sm btn-outline-success like-btn rounded-pill" data-comment-id="${comment.id}" data-bs-toggle="tooltip" title="Curtir este comentário">
                                <i class="bi bi-heart me-1"></i>
                                <span class="like-count">${comment.likes_count || 0}</span>
                            </button>
                        </div>
                        <small class="text-muted">
                            <i class="bi bi-chat-dots me-1"></i>
                            <span class="comment-thread-count">0 respostas</span>
                        </small>
                    </div>
                </div>
            </div>
        </div>`;
 
    const commentsContainer = document.getElementById(`comments-${comment.post}`);
    if (commentsContainer) {
        commentsContainer.appendChild(commentCard);
        commentsContainer.classList.remove('hidden');
 
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}
 
// Expose function globally for non-module loading
window.addCommentToHTML = addCommentToHTML;
