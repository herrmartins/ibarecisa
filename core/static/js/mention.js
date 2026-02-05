/**
 * Mention functionality using Alpine.js
 * Shows a dropdown menu when typing @ with keyboard navigation
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('mentionManager', (textareaId) => ({
        textareaId: textareaId,
        textarea: null,
        menu: null,
        users: [],
        filteredUsers: [],
        selectedIndex: -1,
        mentionStart: -1,
        searchQuery: '',
        showMenu: false,
        cursorX: 0,
        cursorY: 0,

        init() {
            this.textarea = document.getElementById(this.textareaId);
            if (!this.textarea) {
                console.error(`Textarea with id "${this.textareaId}" not found`);
                return;
            }

            this.textarea.addEventListener('input', this.handleInput.bind(this));
            this.textarea.addEventListener('keydown', this.handleKeydown.bind(this));
            this.textarea.addEventListener('click', this.handleClick.bind(this));
            this.textarea.addEventListener('blur', this.handleBlur.bind(this));

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!this.$refs.menu.contains(e.target) && e.target !== this.textarea) {
                    this.showMenu = false;
                }
            });
        },

        handleInput(e) {
            const cursorPosition = this.textarea.selectionStart;
            const textBeforeCursor = this.textarea.value.substring(0, cursorPosition);

            // Find the last @ symbol before cursor
            const lastAtIndex = textBeforeCursor.lastIndexOf('@');

            if (lastAtIndex === -1) {
                this.showMenu = false;
                return;
            }

            // Check if there's a space between @ and cursor
            const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);
            if (textAfterAt.includes(' ')) {
                this.showMenu = false;
                return;
            }

            this.mentionStart = lastAtIndex;
            this.searchQuery = textAfterAt;

            // Update cursor position for menu positioning
            this.updateCursorPosition();

            // Debounce the search
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.searchUsers(this.searchQuery);
            }, 300);
        },

        updateCursorPosition() {
            const rect = this.textarea.getBoundingClientRect();
            const cursorPosition = this.textarea.selectionStart;
            const textBeforeCursor = this.textarea.value.substring(0, cursorPosition);
            const lines = textBeforeCursor.split('\n');
            const currentLine = lines.length - 1;

            const lineHeight = parseInt(window.getComputedStyle(this.textarea).lineHeight) || 24;
            const charWidth = parseInt(window.getComputedStyle(this.textarea).fontSize) || 16;

            this.cursorX = rect.left + (currentLine * charWidth) + window.scrollX;
            this.cursorY = rect.top + (currentLine * lineHeight) + lineHeight + window.scrollY;
        },

        async searchUsers(query) {
            try {
                const url = new URL('/api/mention-users', window.location.origin);
                if (query) {
                    url.searchParams.append('q', query);
                }

                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error('Failed to fetch users');
                }

                const data = await response.json();
                this.users = data;
                this.filteredUsers = this.users.slice(0, 10);
                this.selectedIndex = 0;

                if (this.filteredUsers.length > 0) {
                    this.showMenu = true;
                } else {
                    this.showMenu = false;
                }
            } catch (error) {
                console.error('Error fetching users:', error);
                this.showMenu = false;
            }
        },

        handleKeydown(e) {
            if (!this.showMenu) return;

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredUsers.length - 1);
                    break;

                case 'ArrowUp':
                    e.preventDefault();
                    this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
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
                    this.showMenu = false;
                    break;
            }
        },

        handleClick(e) {
            const cursorPosition = this.textarea.selectionStart;
            const textBeforeCursor = this.textarea.value.substring(0, cursorPosition);
            const lastAtIndex = textBeforeCursor.lastIndexOf('@');

            if (lastAtIndex === -1) {
                this.showMenu = false;
            }
        },

        handleBlur() {
            // Delay hiding to allow click events
            setTimeout(() => {
                this.showMenu = false;
            }, 200);
        },

        selectUser(user) {
            const fullName = `${user.first_name} ${user.last_name}`.trim();
            const cursorPosition = this.textarea.selectionStart;
            const textBeforeCursor = this.textarea.value.substring(0, cursorPosition);
            const textAfterCursor = this.textarea.value.substring(cursorPosition);

            // Find the @ position
            const lastAtIndex = textBeforeCursor.lastIndexOf('@');

            // Replace @query with fullName (without @)
            const newText = textBeforeCursor.substring(0, lastAtIndex) + `${fullName} ` + textAfterCursor;

            this.textarea.value = newText;

            // Set cursor position after the mention
            const newCursorPosition = lastAtIndex + fullName.length + 1;
            this.textarea.setSelectionRange(newCursorPosition, newCursorPosition);
            this.textarea.focus();

            this.showMenu = false;

            // Trigger input event
            this.textarea.dispatchEvent(new Event('input', { bubbles: true }));
        },

        getHighlightedName(user, query) {
            const fullName = `${user.first_name} ${user.last_name}`.trim();
            if (!query) return fullName;
            const regex = new RegExp(`(${query})`, 'gi');
            return fullName.replace(regex, '<strong>$1</strong>');
        },

        getUserType(user) {
            return user.type === 'STAFF' ? 'Equipe' : 'Membro';
        }
    }));
});

// Initialize for prompt textarea when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Alpine will auto-initialize from the data attribute
});
