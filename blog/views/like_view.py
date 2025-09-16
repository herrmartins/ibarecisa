from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from blog.models import Post, Comment
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

    # Get likers data for responsive UI
    likers = []
    for liker in post.likes.all()[:5]:  # Limit to 5 for performance
        likers.append({
            'id': liker.id,
            'first_name': liker.first_name,
            'last_name': liker.last_name,
            'profile_image': liker.profile_image.url if liker.profile_image else None
        })

    return JsonResponse({
        'liked': liked,
        'like_count': post.likes.count(),
        'likers': likers,
        'has_more_likers': post.likes.count() > 5
    })


@login_required
@require_POST
def toggle_comment_like(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)

    user = request.user

    if user in comment.likes.all():
        comment.likes.remove(user)
        liked = False
    else:
        comment.likes.add(user)
        liked = True

    return JsonResponse({
        'liked': liked,
        'like_count': comment.likes.count()
    })