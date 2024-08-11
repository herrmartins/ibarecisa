from rest_framework import serializers
from secretarial.models import (
    MinuteExcerptsModel,
    MinuteTemplateModel,
    MeetingMinuteModel,
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
        fields = (
            "__all__"  # Ensure 'acquittance_doc' is included if '__all__' is not used
        )

    # # If you need custom validation or handling for the uploaded file, add it here
    # def validate_acquittance_doc(self, value):
    #     """
    #     Add any custom validation for your file here, e.g., checking file size, type, etc.
    #     """
    #     return value


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
