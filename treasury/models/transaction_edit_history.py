from django.db import models
from core.models import BaseModel
from users.models import CustomUser
from django.utils import timezone
from treasury.models import TransactionModel
# Actually it also includes delete...


class TransactionEditHistory(BaseModel):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    transaction = models.ForeignKey(
        TransactionModel, on_delete=models.SET_NULL, null=True, blank=True)
    original_description = models.CharField(max_length=255)
    original_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    original_date = models.DateField()
    edited_description = models.CharField(max_length=255)
    edited_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    edited_date = models.DateTimeField(default=timezone.now)
    previous_user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="previous_edits"
    )

    class Meta:
        verbose_name = "Histórico de Edição de Transação"
        verbose_name_plural = "Históricos de Edição de Transações"

    def __str__(self):
        return f"{self.original_description} - {self.edited_description} - {self.original_amount} - {self.edited_amount}"
