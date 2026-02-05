/**
 * Mention functionality for textarea
 * Shows a dropdown menu when typing @ with keyboard navigation
 */

class MentionManager {
    constructor(textareaId, options = {}) {
        this.textarea = document.getElementById(textareaId);
        if (!this.textarea) {
            console.error(`Textarea with id "${textareaId}" not found`);
            return;
        }

        this.apiUrl = options.apiUrl || '/api/mention-users';
        this.menuClass = options.menuClass || 'mention-menu';
        this.itemClass = options.itemClass || 'mention-item';
        this.activeClass = options.activeClass || 'mention-item-active';
        this.maxResults = options.maxResults || 10;
        this.debounceDelay = options.debounceDelay || 300;

        this.menu = null;
        this.users = [];
        this.filteredUsers = [];
        this.selectedIndex = -1;
        this.mentionStart = -1;
        this.searchQuery = '';
        this.debounceTimer = null;

        this.init();
    }

    init() {
        // Create menu element
        this.createMenu();

        // Bind events
        this.textarea.addEventListener('input', this.handleInput.bind(this));
        this.textarea.addEventListener('keydown', this.handleKeydown.bind(this));
        this.textarea.addEventListener('click', this.handleClick.bind(this));
        this.textarea.addEventListener('blur', this.handleBlur.bind(this));

        // Close menu when clicking outside
        document.addEventListener('click', this.handleDocumentClick.bind(this));
    }

    createMenu() {
        this.menu = document.createElement('div');
        this.menu.className = this.menuClass;
        this.menu.style.display = 'none';
        document.body.appendChild(this.menu);
    }

    handleInput(e) {
        const cursorPosition = this.textarea.selectionStart;
        const textBeforeCursor = this.textarea.value.substring(0, cursorPosition);

        // Find the last @ symbol before cursor
        const lastAtIndex = textBeforeCursor.lastIndexOf('@');

        if (lastAtIndex === -1) {
            this.hideMenu();
            return;
        }

        // Check if there's a space between @ and cursor
        const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);
        if (textAfterAt.includes(' ')) {
            this.hideMenu();
            return;
        }

        this.mentionStart = lastAtIndex;
        this.searchQuery = textAfterAt;

        // Debounce the search
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.searchUsers(this.searchQuery);
        }, this.debounceDelay);
    }

    async searchUsers(query) {
        try {
            const url = new URL(this.apiUrl, window.location.origin);
            if (query) {
                url.searchParams.append('q', query);
            }

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to fetch users');
            }

            const data = await response.json();
            this.users = data;
            this.filteredUsers = this.users.slice(0, this.maxResults);
            this.selectedIndex = 0;

            if (this.filteredUsers.length > 0) {
                this.showMenu();
                this.renderMenu();
            } else {
                this.hideMenu();
            }
        } catch (error) {
            console.error('Error fetching users:', error);
            this.hideMenu();
        }
    }

    showMenu() {
        this.menu.style.display = 'block';
        this.positionMenu();
    }

    hideMenu() {
        this.menu.style.display = 'none';
        this.selectedIndex = -1;
    }

    positionMenu() {
        const rect = this.textarea.getBoundingClientRect();
        const cursorPosition = this.textarea.selectionStart;

        // Calculate cursor position
        const textBeforeCursor = this.textarea.value.substring(0, cursorPosition);
        const lines = textBeforeCursor.split('\n');
        const currentLine = lines.length - 1;
        const currentLineText = lines[currentLine];

        // Approximate cursor position (this is a rough estimate)
        const lineHeight = parseInt(window.getComputedStyle(this.textarea).lineHeight) || 24;
        const charWidth = parseInt(window.getComputedStyle(this.textarea).fontSize) || 16;

        const top = rect.top + (currentLine * lineHeight) + lineHeight + window.scrollY;
        const left = rect.left + (currentLineText.length * charWidth) + window.scrollX;

        // Adjust if menu would go off screen
        const menuRect = this.menu.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let adjustedLeft = left;
        let adjustedTop = top;

        if (left + menuRect.width > viewportWidth) {
            adjustedLeft = viewportWidth - menuRect.width - 10;
        }

        if (top + menuRect.height > viewportHeight) {
            adjustedTop = top - menuRect.height - lineHeight;
        }

        this.menu.style.left = `${adjustedLeft}px`;
        this.menu.style.top = `${adjustedTop}px`;
    }

    renderMenu() {
        this.menu.innerHTML = '';

        this.filteredUsers.forEach((user, index) => {
            const item = document.createElement('div');
            item.className = this.itemClass;
            if (index === this.selectedIndex) {
                item.classList.add(this.activeClass);
            }

            const fullName = `${user.first_name} ${user.last_name}`.trim();
            const userType = user.type === 'STAFF' ? 'Equipe' : 'Membro';

            item.innerHTML = `
                <div class="mention-item-content">
                    <span class="mention-item-name">${this.highlightMatch(fullName, this.searchQuery)}</span>
                    <span class="mention-item-type">${userType}</span>
                </div>
            `;

            item.addEventListener('click', () => this.selectUser(user));
            item.addEventListener('mouseenter', () => {
                this.selectedIndex = index;
                this.updateActiveItem();
            });

            this.menu.appendChild(item);
        });
    }

    highlightMatch(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    updateActiveItem() {
        const items = this.menu.querySelectorAll(`.${this.itemClass}`);
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add(this.activeClass);
            } else {
                item.classList.remove(this.activeClass);
            }
        });
    }

    handleKeydown(e) {
        if (this.menu.style.display === 'none') {
            return;
        }

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredUsers.length - 1);
                this.updateActiveItem();
                break;

            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.updateActiveItem();
                break;

            case 'Enter':
            case 'Tab':
                e.preventDefault();
                if (this.selectedIndex >= 0 && this.selectedIndex < this.filteredUsers.length) {
                    this.selectUser(this.filteredUsers[this.selectedIndex]);
                }
                break;

            case 'Escape':
                e.preventDefault();
                this.hideMenu();
                break;
        }
    }

    handleClick() {
        // Check if click is outside the mention context
        const cursorPosition = this.textarea.selectionStart;
        const textBeforeCursor = this.textarea.value.substring(0, cursorPosition);
        const lastAtIndex = textBeforeCursor.lastIndexOf('@');

        if (lastAtIndex === -1) {
            this.hideMenu();
        }
    }

    handleBlur(e) {
        // Delay hiding to allow click events on menu items
        setTimeout(() => {
            this.hideMenu();
        }, 200);
    }

    handleDocumentClick(e) {
        if (!this.menu.contains(e.target) && e.target !== this.textarea) {
            this.hideMenu();
        }
    }

    selectUser(user) {
        const fullName = `${user.first_name} ${user.last_name}`.trim();
        const cursorPosition = this.textarea.selectionStart;
        const textBeforeCursor = this.textarea.value.substring(0, cursorPosition);
        const textAfterCursor = this.textarea.value.substring(cursorPosition);

        // Find the @ position
        const lastAtIndex = textBeforeCursor.lastIndexOf('@');

        // Replace @query with @fullName
        const newText = textBeforeCursor.substring(0, lastAtIndex) + `@${fullName} ` + textAfterCursor;

        this.textarea.value = newText;

        // Set cursor position after the mention
        const newCursorPosition = lastAtIndex + fullName.length + 2;
        this.textarea.setSelectionRange(newCursorPosition, newCursorPosition);
        this.textarea.focus();

        this.hideMenu();

        // Trigger input event to notify any listeners
        this.textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    destroy() {
        if (this.menu) {
            this.menu.remove();
        }
        document.removeEventListener('click', this.handleDocumentClick.bind(this));
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize mention manager for the prompt textarea
    const promptTextarea = document.getElementById('prompt');
    if (promptTextarea) {
        window.mentionManager = new MentionManager('prompt', {
            apiUrl: '/api/mention-users',
            maxResults: 10,
            debounceDelay: 300
        });
    }
});
