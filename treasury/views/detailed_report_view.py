from django.views.generic import MonthArchiveView
from treasury.models import TransactionModel, MonthlyBalance, MonthlyReportModel
from dateutil.relativedelta import relativedelta
from datetime import date
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import MultipleObjectsReturned


class TransactionMonthArchiveView(PermissionRequiredMixin, MonthArchiveView):
    permission_required = "treasury.view_transactionmodel"
    model = TransactionModel
    date_field = "date"
    month_format = "%m"
    allow_future = False
    template_name = "treasury/detailed_report.html"
    context_object_name = "finance_entries"

    def get(self, request, *args, **kwargs):
        # Get the year and month from the URL parameters
        year = self.get_year()
        month = self.get_month()

        # Check if there are any transactions for the given month and year
        transactions_exist = TransactionModel.objects.filter(
            date__year=year, date__month=month
        ).exists()

        # If no transactions exist, add a message and redirect
        if not transactions_exist:
            messages.info(request, "Não há transações para o mês selecionado.")
            return redirect('/treasury/reports')

        # If transactions exist, proceed with the normal flow
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["year"] = self.get_year()
        context["month"] = self.get_month()
        subtotal = []
        previous_month_balance = 0
        current_date = date.today()
        not_current_date = True

        try:
            report = MonthlyReportModel.objects.get(
                month__month=context["month"], month__year=context["year"])
            context["is_report"] = True
        except MonthlyReportModel.DoesNotExist:
            context["is_report"] = False
        except MultipleObjectsReturned:
            context["is_report"] = True
            messages.info(
                self.request, "Há mais de um relatório analítico para este mês, verifique o(s) incorreto(s) e o(s) delete...")

        if (
            current_date.month == context["month"]
            and current_date.year == context["year"]
        ):
            not_current_date = False

        transactions = TransactionModel.objects.filter(
            date__month=context["month"], date__year=context["year"]
        ).order_by("date")

        monthly_sum = transactions.aggregate(total_amount=Sum("amount"))
        total_amount_monthly_sum = monthly_sum.get("total_amount", 0)
        formatted_monthly_sum = "{:.2f}".format(total_amount_monthly_sum)

        previous_month = date(self.get_year(), self.get_month(), 1)

        previous_month += relativedelta(months=-1)
        try:
            balance_for_calc = MonthlyBalance.objects.get(
                month=previous_month).balance
            previous_month_balance = balance_for_calc
        except MonthlyBalance.DoesNotExist:
            balance_for_calc = 0

        for fe in transactions:
            balance_for_calc += fe.amount
            subtotal.append(balance_for_calc)

        context["total"] = balance_for_calc
        context["subtotal"] = subtotal
        context["finance_entries"] = transactions
        context["counter"] = 0
        context["balance"] = previous_month_balance
        context["monthly_result"] = formatted_monthly_sum
        context["ncd"] = not_current_date

        return context
