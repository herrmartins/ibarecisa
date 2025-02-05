from django.views import View
from django.http import JsonResponse
from worship.models import SongFile

class SongFileListView(View):
    def get(self, request, *args, **kwargs):
        song_id = request.GET.get('songId')
        if not song_id:
            return JsonResponse({'success': False, 'error': 'A canção não tem ID.'}, status=400)
        
        song_files = SongFile.objects.filter(song_id=song_id)
        results = []
        for file in song_files:
            results.append({
                'id': file.id,
                'file_type': file.file_type,
                'description': file.description,
                'file_title': file.file_title,
                'url': file.file.url,
            })
        
        return JsonResponse({'success': True, 'results': results})
