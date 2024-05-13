from django.db import models
from users.models import CustomUser
from core.models import BaseModel
from ckeditor.fields import RichTextField
from blog.models import Category
from django.db.models.signals import pre_save
from django.dispatch import receiver
from datetime import datetime


class Post(BaseModel):
    title = models.CharField(max_length=200, null=False, blank=False)
    content = RichTextField(null=False, blank=False)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    summary = models.CharField(max_length=500, null=True, blank=True)
    keywords = models.CharField(max_length=200, null=True, blank=True)
    likes = models.ManyToManyField(
        CustomUser, related_name='liked_posts', blank=True)
    categories = models.ManyToManyField(
        Category, related_name='posts', blank=True)

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self):
        return self.title


@receiver(pre_save, sender=Post)
def update_post_modified_date(sender, instance, **kwargs):
    current_date = datetime.now().date()
    if instance.pk:
        pre_save.disconnect(update_post_modified_date, sender=Post)
        instance.modified = current_date
        instance.save()
        pre_save.connect(update_post_modified_date, sender=Post)
