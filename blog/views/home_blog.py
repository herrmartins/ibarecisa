from django.views.generic import ListView
from blog.models import Post


class BlogHomeView(ListView):
    template_name = 'blog/home.html'
    model = Post
    context_object_name = 'posts'
    paginate_by = 5
    ordering = ['-created', '-id']
