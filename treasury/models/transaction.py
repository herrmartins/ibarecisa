from django.db import models
from core.models import BaseModel
from django.utils import timezone
from django.core.exceptions import ValidationError
from django_resized import ResizedImageField
from treasury.utils import custom_upload_to
from django.core.files.storage import default_storage
import os


class TransactionModel(BaseModel):
    user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    category = models.ForeignKey(
        "treasury.CategoryModel", on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_positive = models.BooleanField(default=True)
    date = models.DateField()

    acquittance_doc = ResizedImageField(
        size=[1200, 850], upload_to=custom_upload_to,
        quality=75, blank=True, null=True, force_format='JPEG'
    )

    edit_history = models.ManyToManyField(
        "treasury.TransactionEditHistory", blank=True)

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"

    def __str__(self):
        return f"{self.date} - {self.description} - R$ {self.amount}"

    def save(self, *args, **kwargs):
        today = timezone.now().date()
        if self.date > today:
            raise ValidationError("Não se pode adicionar transação com data futura...")

        from treasury.models import MonthlyBalance
        try:
            MonthlyBalance.objects.get(is_first_month=True)
        except MonthlyBalance.DoesNotExist:
            raise ValidationError(
                "Não se pode adicionar transações sem um balanço mensal...")

        if self.pk:
            old_doc = TransactionModel.objects.filter(
                pk=self.pk).values_list('acquittance_doc', flat=True).first()
            if old_doc and old_doc != self.acquittance_doc.name:
                try:
                    default_storage.delete(old_doc)
                except Exception as e:
                    print(f"Failed to delete old document: {e}")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.acquittance_doc and self.acquittance_doc.name:
            if os.path.isfile(self.acquittance_doc.path):
                os.remove(self.acquittance_doc.path)

        super(TransactionModel, self).delete(*args, **kwargs)
