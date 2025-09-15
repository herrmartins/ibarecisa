
export function addCommentToHTML(comment) {
    const commentCard = document.createElement('div');
    commentCard.className = 'card ml-2 my-2 p-2 card-no-border';
    commentCard.setAttribute('data-comment-id', comment.id);

    const replyButton = `<button class="btn btn-sm btn-outline-primary reply-btn" data-comment-id="${comment.id}">Responder</button>`;
    commentCard.innerHTML = `
        <div class="card-body">
            <p class="card-text">${comment.content}</p>
            <div class="d-flex justify-content-between">
                <div class="d-flex flex-row align-items-center">
                    ${
                        comment.user_photo
                            ? `<img src="${comment.user_photo}" alt="avatar" width="25" height="25" />`
                            : ""
                    }
                    <p class="small mb-0 ms-2">${comment.author_name}</p>
                </div>
                <div class="d-flex flex-row align-items-center">
                    ${replyButton}
                    <p class="small text-muted mb-0 ms-2">Like</p>
                    <i class="bi bi-hand-thumbs-up" style="margin-top: -0.16rem;"></i>
                </div>
            </div>
        </div>`;

    const commentsContainer = document.getElementById(`comments-${comment.post}`);
    if (commentsContainer) {
        commentsContainer.appendChild(commentCard);
        commentsContainer.classList.remove('hidden');
    }
}
