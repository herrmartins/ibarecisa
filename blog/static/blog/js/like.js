import { getCookie } from '/static/js/get_cookie.js';

document.addEventListener('DOMContentLoaded', function() {
    const likeButtons = document.querySelectorAll('.like-btn');

    likeButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            const postId = button.getAttribute('data-post-id');
            const csrfToken = getCookie('csrftoken');
 
            const likeUrl = button.getAttribute('data-like-url') || `/blog/like/${postId}/`;
 
            fetch(likeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const likeCount = document.getElementById(`like-count-${postId}`);
                if (likeCount) {
                    likeCount.textContent = data.like_count;
                }
 
                // Toggle the 'fill' class on the inner icon, not on the click event target.
                // This covers clicks on button, icon or child elements.
                const icon = button.querySelector('.bi');
                if (icon) {
                    if (data.liked) {
                        icon.classList.add('fill');
                    } else {
                        icon.classList.remove('fill');
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        });

        // Hover to show tooltip
        const tooltip = document.getElementById(`likers-${button.getAttribute('data-post-id')}`);
        button.addEventListener('mouseenter', () => {
            if (tooltip) {
                tooltip.style.display = 'flex';
            }
        });
        button.addEventListener('mouseleave', () => {
            if (tooltip) {
                tooltip.style.display = 'none';
            }
        });
    });
});