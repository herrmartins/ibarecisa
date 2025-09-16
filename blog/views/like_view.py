from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from blog.models import Post
from django.core.exceptions import ObjectDoesNotExist


@login_required
@require_POST
def toggle_like(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)

    user = request.user

    if user in post.likes.all():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True

    return JsonResponse({
        'liked': liked,
        'like_count': post.likes.count()
    })