// comment_edit.js

document.addEventListener('DOMContentLoaded', function() {
    // Event delegation for edit buttons
    document.addEventListener('click', function(event) {
        if (event.target.closest('.edit-btn')) {
            event.preventDefault();
            const editBtn = event.target.closest('.edit-btn');
            const commentId = editBtn.getAttribute('data-comment-id');
            toggleEditMode(commentId);
        }

        if (event.target.closest('.save-edit-btn')) {
            event.preventDefault();
            const saveBtn = event.target.closest('.save-edit-btn');
            const commentId = saveBtn.getAttribute('data-comment-id');
            saveCommentEdit(commentId);
        }

        if (event.target.closest('.cancel-edit-btn')) {
            event.preventDefault();
            const cancelBtn = event.target.closest('.cancel-edit-btn');
            const commentId = cancelBtn.getAttribute('data-comment-id');
            cancelCommentEdit(commentId);
        }
    });
});

function toggleEditMode(commentId) {
    const commentCard = document.querySelector(`[data-comment-id="${commentId}"]`);
    const commentContent = commentCard.querySelector('.comment-content');

    if (commentCard.classList.contains('editing')) {
        // Already in edit mode, do nothing
        return;
    }

    // Mark as editing
    commentCard.classList.add('editing');

    // Get current content
    const currentContent = commentContent.textContent.trim();

    // Replace content with textarea
    commentContent.innerHTML = `
        <div class="edit-form">
            <textarea class="form-control mb-2" rows="3" id="edit-textarea-${commentId}">${currentContent}</textarea>
            <div class="d-flex gap-2">
                <button class="btn btn-sm btn-success save-edit-btn" data-comment-id="${commentId}">
                    <i class="bi bi-check me-1"></i>Salvar
                </button>
                <button class="btn btn-sm btn-secondary cancel-edit-btn" data-comment-id="${commentId}">
                    <i class="bi bi-x me-1"></i>Cancelar
                </button>
            </div>
        </div>
    `;

    // Focus on textarea
    const textarea = document.getElementById(`edit-textarea-${commentId}`);
    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
}

function saveCommentEdit(commentId) {
    const commentCard = document.querySelector(`[data-comment-id="${commentId}"]`);
    const textarea = document.getElementById(`edit-textarea-${commentId}`);
    const newContent = textarea.value.trim();

    if (!newContent) {
        alert('O comentário não pode ficar vazio.');
        return;
    }

    // Disable buttons during save
    const saveBtn = commentCard.querySelector('.save-edit-btn');
    const cancelBtn = commentCard.querySelector('.cancel-edit-btn');
    saveBtn.disabled = true;
    cancelBtn.disabled = true;
    saveBtn.innerHTML = '<i class="bi bi-hourglass me-1"></i>Salvando...';

    // Send update request
    const csrfToken = getCookie('csrftoken');
    fetch(`/api2/comments/update/${commentId}`, {
        method: 'PATCH',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            content: newContent
        })
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 403) {
                throw new Error('Você não tem permissão para editar este comentário.');
            }
            throw new Error('Erro ao salvar comentário.');
        }
        return response.json();
    })
    .then(data => {
        // Update comment content
        const commentContent = commentCard.querySelector('.comment-content');
        commentContent.textContent = data.content;

        // Remove editing class
        commentCard.classList.remove('editing');

        // Show success message
        showSuccessMessage(commentCard, 'Comentário atualizado com sucesso!');
    })
    .catch(error => {
        console.error('Error updating comment:', error);
        alert(error.message || 'Erro ao salvar comentário. Tente novamente.');
    })
    .finally(() => {
        // Re-enable buttons
        saveBtn.disabled = false;
        cancelBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-check me-1"></i>Salvar';
    });
}

function cancelCommentEdit(commentId) {
    const commentCard = document.querySelector(`[data-comment-id="${commentId}"]`);
    const commentContent = commentCard.querySelector('.comment-content');

    // Get original content from data attribute or fetch again
    const originalContent = commentContent.getAttribute('data-original-content') ||
                           commentContent.textContent.trim();

    // Restore original content
    commentContent.textContent = originalContent;

    // Remove editing class
    commentCard.classList.remove('editing');
}

function showSuccessMessage(commentCard, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-absolute';
    alertDiv.style.cssText = 'top: 10px; right: 10px; z-index: 1000; min-width: 250px;';
    alertDiv.innerHTML = `
        <i class="bi bi-check-circle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    commentCard.style.position = 'relative';
    commentCard.appendChild(alertDiv);

    // Auto remove after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}