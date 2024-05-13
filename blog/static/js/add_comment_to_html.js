
export function addCommentToHTML(comment) {
    // Create the main comment card div
    const commentCard = document.createElement('div');
    commentCard.className = 'card ml-2 my-2 p-2 card-no-border';

    // Construct the inner HTML for the comment card
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
                    <p class="small text-muted mb-0">Like</p>
                    <i class="bi bi-hand-thumbs-up" style="margin-top: -0.16rem;"></i>
                </div>
            </div>
        </div>`;

    // Find the comments container for this particular post
    const commentsContainer = document.getElementById(`comments-${comment.post}`);
    if (commentsContainer) {
        // Append the new comment card to the comments container
        commentsContainer.appendChild(commentCard);

        // Make sure the comments container is visible
        commentsContainer.classList.remove('hidden');
    }
}
