from django.http import JsonResponse
from django.views import View
from worship.models import Composer

class ComposerListView(View):
    def get(self, request):
        query = request.GET.get("q", "")
        composers = Composer.objects.filter(name__icontains=query)[:10]
        data = [{"id": composer.id, "text": composer.name} for composer in composers]
        return JsonResponse({"results": data})

