from rest_framework import serializers
from secretarial.models import (
    MinuteExcerptsModel,
    MinuteTemplateModel,
    MeetingMinuteModel,
    MinuteProjectModel,
)
from treasury.models import TransactionModel, CategoryModel
from users.models import CustomUser


class MinuteExcerptsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinuteExcerptsModel
        fields = "__all__"


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"


class MinuteTemplateModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinuteTemplateModel
        fields = "__all__"


class MeetingMinuteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingMinuteModel
        fields = "__all__"


class MinuteProjectModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinuteProjectModel
        fields = "__all__"


class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = "__all__"


class TransactionCatModelSerializer(serializers.ModelSerializer):
    category = CategoryModelSerializer()

    class Meta:
        model = TransactionModel
        fields = "__all__"


class TransactionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionModel
        fields = '__all__' 


class BalanceSerializer(serializers.Serializer):
    current_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_month_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    unaware_month_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    sum_negative_transactions = serializers.DecimalField(
        max_digits=10, decimal_places=2
    )
    sum_positive_transactions = serializers.DecimalField(
        max_digits=10, decimal_places=2
    )
