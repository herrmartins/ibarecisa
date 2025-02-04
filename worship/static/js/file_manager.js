document.addEventListener('alpine:init', () => {
    Alpine.data('fileManager', (songId) => ({
      songId: songId,
      files: [],
      selectedFile: null,
      fileType: '',
      description: '',
      file_title: '',
      
      init() {
        this.fetchSongFiles();
      },
  
      async fetchSongFiles() {
        try {
          const response = await fetch(`/worship/song-files/?songId=${this.songId}`);
          const data = await response.json();
          if (data.success) {
            this.files = data.results;
            this.$refs.fileInput.value = '';
            this.selectedFile = null;
            this.fileType = '';
            this.file_title = '';
            this.description = '';
          } else {
            console.error('Error fetching files:', data.error);
          }
        } catch (error) {
          console.error('Error fetching song files:', error);
        }
      },
  
      async submitFile() {
        if (!this.selectedFile) {
          alert('Por favor, selecione um arquivo.');
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
          if (data.success) {
            this.fetchSongFiles();
          } else {
            alert(`Erro ao enviar arquivo: ${data.error || 'Erro desconhecido'}`);
          }
        } catch (error) {
          alert(`Erro ao enviar arquivo: ${error.message}`);
        }
      },
    }));
  });