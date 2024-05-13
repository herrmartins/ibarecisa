from django.contrib import admin
from blog.models import Category, Comment, Post

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Category)
