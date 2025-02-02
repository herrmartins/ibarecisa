document.addEventListener('alpine:init', () => {
    Alpine.data('songSearch', () => ({
        query: '',
        results: {
            title_matches: [],
            artist_matches: [],
            lyrics_matches: [],
            theme_matches: [],
        },
        getSongDetailUrl(songId) {
            return `/worship/song/${songId}`;
        },
        searchSongs() {
            fetch(`/worship/songs/search?q=${encodeURIComponent(this.query)}`)
                .then(response => response.json())
                .then(data => {
                    console.log('Search results:', data);
                    this.results = data;
                })
                .catch(error => console.error('Error fetching search results:', error));
        },
    }));

    Alpine.data('songForm', () => ({
        title: '',
        artist: '',
        theme: '',
        hymnal: '',
        lyrics: '',
        message: '',
        artists: [],
        themes: [],
        hymnals: [],

        initAddSongForm() {
            this.fetchArtists();
            this.fetchThemes();
            this.fetchHymnals();
        },

        init() {
            const quill = new Quill('#editor', {
                theme: 'snow'
            });
            quill.on('text-change', () => {
                this.lyrics = quill.root.innerHTML;
                console.log('Updated lyrics:', this.lyrics);
            });
        },

        async fetchArtists() {
            try {
                const response = await fetch('/worship/composers/');
                const data = await response.json();
                console.log('Fetched composers:', data);
                this.artists = data.results;
            } catch (error) {
                console.error('Error fetching artists:', error);
            }
        },

        async fetchThemes() {
            try {
                const response = await fetch('/worship/themes/');
                const data = await response.json();
                console.log('Fetched themes:', data);
                this.themes = data.results;
            } catch (error) {
                console.error('Error fetching themes:', error);
            }
        },

        async fetchHymnals() {
            try {
                const response = await fetch('/worship/hymnals/');
                const data = await response.json();
                console.log('Fetched hymnals:', data);
                this.hymnals = data.results;
            } catch (error) {
                console.error('Error fetching hymnals:', error);
            }
        },

        resetForm() {
            this.title = '';
            this.artist = '';
            this.theme = '';
            this.hymnal = '';
            this.lyrics = '';
            this.message = '';
        },

        async submitForm() {
            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const response = await fetch('/worship/song-add/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({
                        title: this.title,
                        artist: this.artist,
                        theme: this.theme,
                        hymnal: this.hymnal,
                        lyrics: this.lyrics,
                    }),
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    this.message = 'Canção adicionada com sucesso!';
                    alert(this.message);
                    this.resetForm();
                } else {
                    this.message = `Erro: ${data.error || 'Erro desconhecido'}`;
                    alert(this.message);
                }
            } catch (error) {
                this.message = `Erro ao enviar os dados: ${error.message}`;
                alert(this.message);
            }
        },
    }));
});
