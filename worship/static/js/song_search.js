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
      key: '',
      metrics: '',
      message: '',
      success: false,
  
      songId: null,
      files: [],
      selectedFile: null,
      fileType: '',
      file_title: '',
      description: '',
  
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
        });
        this.$watch('key', (value) => {
          console.log('key:', this.key);
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
        this.metrics = '';
        this.key = '';
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
              metrics: this.metrics,
              key: this.key,
            }),
          });
  
          const data = await response.json();
  
          if (response.ok && data.success) {
            this.message = 'Canção adicionada com sucesso!';
            this.success = true;
            console.log('Song added:', data?.song_id, data);
            this.songId = data?.song_id;
            this.fetchSongFiles();
  
            setTimeout(() => {
              this.success = false;
            }, 3000);
          } else {
            this.message = `Erro: ${data.error || 'Erro desconhecido'}`;
            this.success = false;
            alert(this.message);
          }
        } catch (error) {
          this.message = `Erro ao enviar os dados: ${error.message}`;
          this.success = false;
          alert(this.message);
        }
      },
  
      async fetchSongFiles() {
        if (!this.songId) return;
        try {
          const response = await fetch(`/worship/song-files/?songId=${this.songId}`);
          const data = await response.json();
          this.files = data.results;
          console.log('Fetched song files:', data);
        } catch (error) {
          console.error('Erro carregando os arquivos:', error);
        }
      },
  
      async submitFile() {
        if (!this.selectedFile) {
          alert('Por favor, selecione um arquivo.');
          return;
        }
        if (!this.songId) {
          alert('A canção ainda não foi criada.');
          return;
        }
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const formData = new FormData();
        formData.append('song', this.songId);
        formData.append('file', this.selectedFile);
        formData.append('file_type', this.fileType);
        formData.append('file_title', this.file_title);
        formData.append('description', this.description);
  
        try {
          const response = await fetch('/worship/song-files/add/', {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrfToken,
            },
            body: formData,
          });
          const data = await response.json();
          if (response.ok && data.success) {
            alert('Arquivo enviado com sucesso!');
            this.fetchSongFiles();
            this.selectedFile = null;
            this.fileType = '';
            this.description = '';
            this.title = '';
          } else {
            alert(`Erro ao enviar arquivo: ${data.error || 'Erro desconhecido'}`);
          }
        } catch (error) {
          alert(`Erro ao enviar arquivo: ${error.message}`);
        }
      },
    }));
  });  