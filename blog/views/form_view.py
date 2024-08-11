from django.views.generic.edit import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from blog.forms import PostForm
from blog.models import Post


class PostFormView(PermissionRequiredMixin, FormView):
    permission_required = "blog.add_post"
    template_name = "blog/form.html"
    form_class = PostForm
    context_object_name = "obj"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        post_id = self.kwargs.get("pk")
        post = Post.objects.filter(id=post_id).first()
        kwargs["instance"] = post
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_id = self.kwargs.get("pk")
        post = Post.objects.filter(id=post_id).first()
        context["instance"] = post
        return context

    def get_initial(self):
        post_id = self.kwargs.get("pk")
        post = Post.objects.filter(id=post_id).first()
        initial_data = super().get_initial()
        if post:
            initial_data["author"] = self.request.user
            initial_data["title"] = post.title
            initial_data["content"] = post.content
            initial_data["summary"] = post.summary
            initial_data["keywords"] = post.keywords

        return initial_data
