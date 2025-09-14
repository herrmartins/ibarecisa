from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import generics, status
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404
from treasury.models import MonthlyBalance
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import (
    MinuteExcerptsSerializer,
    CustomUserSerializer,
    MeetingMinuteModelSerializer,
    MinuteTemplateModelSerializer,
    MinuteProjectModelSerializer,
    TransactionModelSerializer,
    TransactionCatModelSerializer,
    BalanceSerializer,
)
from users.models import CustomUser
from secretarial.models import MinuteExcerptsModel
from secretarial.models import MeetingMinuteModel, MinuteTemplateModel, MinuteProjectModel

from treasury.models import TransactionModel


@api_view(["GET"])
def getCurrentBalance(request):
    current_month = timezone.now().month
    current_year = timezone.now().year

    previous_month = timezone.now() - relativedelta(months=1)

    last_month_balance = MonthlyBalance.objects.get(
        month__month=previous_month.month, month__year=previous_month.year
    )

    transactions_queryset = TransactionModel.objects.filter(
        date__month=current_month, date__year=current_year
    ).order_by("-date")

    positive_transactions_queryset = transactions_queryset.filter(
        is_positive=True)
    negative_transactions_queryset = transactions_queryset.filter(
        is_positive=False)

    unaware_month_balance = sum(t.amount for t in transactions_queryset)
    positive_transactions = sum(
        pt.amount for pt in positive_transactions_queryset)
    negative_transactions = sum(
        nt.amount for nt in negative_transactions_queryset)

    aware_month_balance = last_month_balance.balance + unaware_month_balance

    serializer = BalanceSerializer(
        {
            "current_balance": aware_month_balance,
            "last_month_balance": last_month_balance.balance,
            "unaware_month_balance": unaware_month_balance,
            "sum_negative_transactions": negative_transactions,
            "sum_positive_transactions": positive_transactions,
        }
    )

    return Response(serializer.data)


@api_view(["GET"])
def getData(request):
    excerpts = MinuteExcerptsModel.objects.all()
    serializer = MinuteExcerptsSerializer(excerpts, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def getDetailedData(request, pk):
    excerpt = MinuteExcerptsModel.objects.get(pk=pk)
    excerpt.times_used += 1
    excerpt.save()
    serializer = MinuteExcerptsSerializer(excerpt, many=False)
    return Response(serializer.data)


class TransactionCatListAPIView(generics.ListAPIView):
    serializer_class = TransactionCatModelSerializer

    def get_queryset(self):
        current_month = timezone.now().month
        current_year = timezone.now().year

        queryset = TransactionModel.objects.filter(
            date__month=current_month, date__year=current_year
        ).order_by("-date")
        return queryset


class TransactionsCreateAPIView(generics.CreateAPIView):
    serializer_class = TransactionModelSerializer
    # Enable parsing of multipart/form-data
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("ERRO:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteTransaction(generics.DestroyAPIView):
    queryset = TransactionModel.objects.all()
    serializer_class = TransactionModelSerializer
    lookup_field = "pk"


@api_view(["POST"])
def unifiedSearch(request):
    search_category = request.data.get("category")
    search_criterion = request.data.get("searched")


    if search_category == "users":
        queryset = CustomUser.objects.filter(
            Q(type=CustomUser.Types.SIMPLE_USER)
            | Q(type=CustomUser.Types.ONLY_WORKER)
            | Q(type=CustomUser.Types.CONGREGATED),
            Q(first_name__icontains=search_criterion)
            | Q(last_name__icontains=search_criterion),
        )
        serialized_data = CustomUserSerializer(queryset, many=True)
        return Response(serialized_data.data)

    elif search_category == "minutes":

        search_terms = [search_criterion]

        if 'í' in search_criterion:
            search_terms.append(search_criterion.replace('í', '&iacute;'))
        if 'á' in search_criterion:
            search_terms.append(search_criterion.replace('á', '&aacute;'))
        if 'é' in search_criterion:
            search_terms.append(search_criterion.replace('é', '&eacute;'))
        if 'ó' in search_criterion:
            search_terms.append(search_criterion.replace('ó', '&oacute;'))
        if 'ú' in search_criterion:
            search_terms.append(search_criterion.replace('ú', '&uacute;'))
        if 'ã' in search_criterion:
            search_terms.append(search_criterion.replace('ã', '&atilde;'))
        if 'õ' in search_criterion:
            search_terms.append(search_criterion.replace('õ', '&otilde;'))
        if 'â' in search_criterion:
            search_terms.append(search_criterion.replace('â', '&acirc;'))
        if 'ê' in search_criterion:
            search_terms.append(search_criterion.replace('ê', '&ecirc;'))
        if 'ô' in search_criterion:
            search_terms.append(search_criterion.replace('ô', '&ocirc;'))

        q_objects = Q()
        for term in search_terms:
            q_objects |= Q(body__icontains=term)

        queryset = MeetingMinuteModel.objects.filter(
            q_objects | Q(meeting_date__icontains=search_criterion)
        ).filter(body__isnull=False).exclude(body__exact='')
        serialized_data = MeetingMinuteModelSerializer(queryset, many=True)

        for data in serialized_data.data:
            president_id = data.get("president")
            if president_id:
                president = get_object_or_404(CustomUser, pk=president_id)
                data["president"] = f"{president.first_name} {president.last_name}"
        return Response(serialized_data.data)

    elif search_category == "templates":
        queryset = MinuteTemplateModel.objects.filter(
            Q(title__icontains=search_criterion) | Q(
                body__icontains=search_criterion)
        )
        serialized_data = MinuteTemplateModelSerializer(queryset, many=True)
        return Response(serialized_data.data)

    elif search_category == "members":
        queryset = CustomUser.objects.filter(
            Q(type=CustomUser.Types.REGULAR) | Q(type=CustomUser.Types.STAFF),
            Q(first_name__icontains=search_criterion)
            | Q(last_name__icontains=search_criterion),
        )
        serialized_data = CustomUserSerializer(queryset, many=True)
        return Response(serialized_data.data)

    elif search_category == "projects":
        queryset = MinuteProjectModel.objects.filter(
            body__icontains=search_criterion)
        serialized_data = MinuteProjectModelSerializer(queryset, many=True)

        for data in serialized_data.data:
            president_id = data.get("president")
            if president_id:
                president = get_object_or_404(CustomUser, pk=president_id)
                data["president"] = f"{president.first_name} {president.last_name}"

        return Response(serialized_data.data)

    else:
        return Response(
            {"error": "Categoria de busca inválida..."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(serialized_data.data)
