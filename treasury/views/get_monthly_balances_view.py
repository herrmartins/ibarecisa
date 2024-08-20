from django.http import JsonResponse
from django.views import View
from treasury.models import MonthlyBalance
from django.db.models.functions import TruncYear, TruncMonth


class GetMonthlyBalancesView(View):
    def get(self, request, *args, **kwargs):
        # Filter out the first month balance
        distinct_years = (
            MonthlyBalance.objects.filter(is_first_month=False)
            .annotate(
                year_annotation=TruncYear("month"), month_annotation=TruncMonth("month")
            )
            .values_list("year_annotation", "month_annotation")
            .distinct()
            .order_by("year_annotation", "month_annotation")
        )

        year_month_map = {}
        for year, month in distinct_years:
            year = year.year
            month = month.month
            if year not in year_month_map:
                year_month_map[year] = []
            year_month_map[year].append(month)

        year_list = sorted(year_month_map.keys())

        return JsonResponse(
            {
                "year_list": year_list,
                "year_month_map": year_month_map,
            }
        )
