from django.contrib.staticfiles.finders import find
from users.models import CustomUser
import json
from django.conf import settings


def context_user_data(request):
    file_path = find("json/church_info.json")

    church_info = {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            church_info = json.load(file)
    except FileNotFoundError:
        print("Erro: File not found")

    if request.user.is_authenticated:
        user = CustomUser.objects.get(pk=request.user.id)
        return {
            "user": user,
            "church_info": church_info,
            "TINYMCE_API_KEY": getattr(settings, 'TINYMCE_API_KEY', ''),
        }
    else:
        return {
            "church_info": church_info,
            "TINYMCE_API_KEY": getattr(settings, 'TINYMCE_API_KEY', ''),
        }
