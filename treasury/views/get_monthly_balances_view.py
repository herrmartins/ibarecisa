from django.http import JsonResponse
from django.views import View
from treasury.models import MonthlyBalance
from django.db.models.functions import TruncYear


class GetMonthlyBalancesView(View):
    def get(self, request, *args, **kwargs):
        distinct_years = (
            MonthlyBalance.objects.annotate(year=TruncYear("month"))
            .values_list("year", flat=True)
            .distinct()
            .order_by("year")
        )
        year_list = [year.year for year in distinct_years]

        return JsonResponse(
            {
                "year_list": year_list,
            }
        )
