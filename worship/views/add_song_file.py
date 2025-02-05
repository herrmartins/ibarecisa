from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from worship.models import Song, SongFile

@require_POST
def add_song_file(request):
    song_id = request.POST.get('song')
    if not song_id:
        return JsonResponse({'success': False, 'error': 'Missing song ID.'}, status=400)
    
    song = get_object_or_404(Song, id=song_id)
    
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'success': False, 'error': 'No file provided.'}, status=400)
    
    file_type = request.POST.get('file_type')
    description = request.POST.get('description', '')
    file_title = request.POST.get('file_title')
    
    song_file = SongFile(
        song=song,
        file=uploaded_file,
        file_type=file_type,
        file_title=file_title,
        description=description
    )
    song_file.save()

    return JsonResponse({
        'success': True,
        'file': {
            'id': song_file.id,
            'file_type': song_file.file_type,
            'description': song_file.description,
            'url': song_file.file.url,
        }
    })
