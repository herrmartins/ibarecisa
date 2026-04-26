from django.http import JsonResponse
from django.views import View
import difflib

from worship.models import Hymnal


def _normalize(value):
    return "".join(ch for ch in (value or "").lower() if ch.isalnum())

class HymnalListView(View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        hymnals = Hymnal.objects.all()[:200]
        if query:
            direct = list(Hymnal.objects.filter(title__icontains=query)[:10])
            normalized_query = _normalize(query)
            scored = []
            for hymnal in hymnals:
                score = difflib.SequenceMatcher(None, normalized_query, _normalize(hymnal.title)).ratio()
                if score >= 0.45:
                    scored.append((score, hymnal))
            scored.sort(key=lambda pair: pair[0], reverse=True)
            fuzzy = [item[1] for item in scored[:10]]
            ordered = []
            seen = set()
            for hymnal in direct + fuzzy:
                if hymnal.id in seen:
                    continue
                seen.add(hymnal.id)
                ordered.append(hymnal)
            hymnals = ordered[:10]
        else:
            hymnals = list(hymnals[:10])
        data = [{"id": hymnal.id, "text": hymnal.title} for hymnal in hymnals]
        return JsonResponse({"results": data})
