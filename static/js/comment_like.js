import { getCookie } from "./get_cookie.js";

document.addEventListener('DOMContentLoaded', function() {
    // Event delegation for comment like buttons
    document.addEventListener('click', function(event) {
        if (event.target.closest('.like-btn') && event.target.closest('.like-btn').hasAttribute('data-comment-id')) {
            event.preventDefault();
            const likeBtn = event.target.closest('.like-btn');
            const commentId = likeBtn.getAttribute('data-comment-id');

            toggleCommentLike(commentId, likeBtn);
        }
    });
});

async function toggleCommentLike(commentId, likeBtn) {
    const isAuthenticated = document.getElementById('user-info') !== null;
    if (!isAuthenticated) {
        alert('Você precisa estar logado para curtir comentários.');
        return;
    }

    const csrfToken = getCookie('csrftoken');
    const likeUrl = `/blog/comment/like/${commentId}/`;

    try {
        const response = await fetch(likeUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Update the like count
        const likeCountSpan = likeBtn.querySelector('.like-count');
        if (likeCountSpan) {
            likeCountSpan.textContent = data.like_count;
        }

        // Toggle visual state (add/remove 'liked' class for styling)
        if (data.liked) {
            likeBtn.classList.add('liked');
        } else {
            likeBtn.classList.remove('liked');
        }

    } catch (error) {
        console.error('Error toggling comment like:', error);
        alert('Erro ao processar curtida. Tente novamente.');
    }
}