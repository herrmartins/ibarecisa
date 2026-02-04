from django.db import models
from core.models import BaseModel
from django.utils import timezone
from django.core.exceptions import ValidationError
from treasury.utils import custom_upload_to
from django.core.files.storage import default_storage
from decimal import Decimal
import os

# Import para S3 (se disponível)
try:
    import boto3
    from django.conf import settings
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class TransactionModel(BaseModel):
    user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    category = models.ForeignKey(
        "treasury.CategoryModel", on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_positive = models.BooleanField(default=True)
    date = models.DateField()

    # FileField simples para aceitar PDF e imagens
    # Nota: usa string literal para evitar problemas com migrations no SQLite
    acquittance_doc = models.FileField(
        upload_to='treasury/receipts/',
        blank=True, null=True
    )

    edit_history = models.ManyToManyField(
        "treasury.TransactionEditHistory", blank=True)

    # Campo para vincular ao período contábil
    accounting_period = models.ForeignKey(
        'treasury.AccountingPeriod',
        on_delete=models.PROTECT,  # Não permite excluir período com transações
        related_name='transactions',
        null=True,  # Temporário durante migração
        blank=True,
        help_text="Período contábil a que esta transação pertence"
    )

    # Tipo de transação
    TRANSACTION_TYPE_CHOICES = [
        ('original', 'Original'),
        ('reversal', 'Estorno'),
    ]
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='original',
        help_text="Tipo da transação (original ou estorno)"
    )

    # Para estornos: aponta para a transação original
    reverses = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversed_by',
        help_text="Para estornos, aponta para a transação original"
    )

    # Quem criou a transação
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_transactions',
        help_text="Usuário que criou a transação"
    )

    # Quando a transação foi criada
    created_at = models.DateTimeField(default=timezone.now)

    # Quando a transação foi modificada pela última vez
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"

    def __str__(self):
        return f"{self.date} - {self.description} - R$ {self.amount}"

    def save(self, *args, **kwargs):
        today = timezone.now().date()
        if self.date > today:
            raise ValidationError("Não se pode adicionar transação com data futura...")

        # Vincular automaticamente ao período contábil se não estiver vinculado
        # Skip during migrations or if AccountingPeriod doesn't exist yet
        if not self.accounting_period:
            try:
                from treasury.models import AccountingPeriod

                # Encontrar ou criar o período para a data da transação
                period_month = self.date.replace(day=1)
                try:
                    period = AccountingPeriod.objects.get(month=period_month)
                except AccountingPeriod.DoesNotExist:
                    # Criar período com opening_balance do período anterior
                    previous_period = None
                    if self.date.month > 1:
                        prev_month = self.date.replace(month=self.date.month - 1, day=1)
                        try:
                            previous_period = AccountingPeriod.objects.get(month=prev_month)
                        except AccountingPeriod.DoesNotExist:
                            pass
                    else:
                        prev_year = self.date.year - 1
                        try:
                            previous_period = AccountingPeriod.objects.get(
                                month=timezone.datetime(prev_year, 12, 1).date()
                            )
                        except (AccountingPeriod.DoesNotExist, ValueError):
                            pass

                    opening_balance = previous_period.closing_balance if previous_period and previous_period.closing_balance else Decimal('0.00')
                    period = AccountingPeriod.objects.create(
                        month=period_month,
                        opening_balance=opening_balance,
                        status='open'
                    )

                self.accounting_period = period
            except Exception:
                # AccountingPeriod might not exist during migrations
                pass

        # Verificar se a transação pode ser editada
        if self.pk:
            # Verificar se o período está fechado
            old_transaction = TransactionModel.objects.filter(pk=self.pk).first()
            if old_transaction and old_transaction.accounting_period:
                if old_transaction.accounting_period.is_closed:
                    # Permitir apenas certos campos em transações de períodos fechados
                    # (isso será tratado pela API, não aqui)
                    pass

            # Limpar documento antigo se foi alterado
            old_doc = TransactionModel.objects.filter(
                pk=self.pk).values_list('acquittance_doc', flat=True).first()
            if old_doc and old_doc != self.acquittance_doc.name:
                try:
                    default_storage.delete(old_doc)
                except Exception as e:
                    print(f"Erro ao deletar documento: {e}")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Deleta o arquivo do comprovante (local ou S3)
        if self.acquittance_doc and self.acquittance_doc.name:
            deleted = False

            # Método 1: Tenta usar o método padrão do Django
            try:
                self.acquittance_doc.delete(save=False)
                deleted = True
            except Exception as e1:
                print(f"[TransactionModel] Erro ao deletar com .delete(): {e1}")

            # Método 2: Se falhou e S3 está configurado, tenta boto3 diretamente
            if not deleted and BOTO3_AVAILABLE:
                try:
                    s3 = boto3.client(
                        's3',
                        endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
                        aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                        aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                        region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
                    )
                    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
                    if bucket_name:
                        s3.delete_object(Bucket=bucket_name, Key=self.acquittance_doc.name)
                        deleted = True
                        print(f"[TransactionModel] Arquivo deletado do S3 via boto3: {self.acquittance_doc.name}")
                except Exception as e2:
                    print(f"[TransactionModel] Erro ao deletar com boto3: {e2}")

            # Método 3: Storage local (fallback)
            if not deleted:
                try:
                    if self.acquittance_doc.storage.exists(self.acquittance_doc.name):
                        self.acquittance_doc.storage.delete(self.acquittance_doc.name)
                        deleted = True
                except Exception as e3:
                    print(f"[TransactionModel] Erro ao deletar com storage: {e3}")

            if not deleted:
                print(f"[TransactionModel] AVISO: Arquivo não foi deletado: {self.acquittance_doc.name}")

        super(TransactionModel, self).delete(*args, **kwargs)

    @property
    def signed_amount(self):
        """Retorna o valor com sinal (positivo ou negativo)."""
        return self.amount if self.is_positive else -self.amount

    @property
    def can_be_edited(self):
        """Verifica se a transação pode ser editada."""
        if not self.accounting_period:
            return True
        return self.accounting_period.is_open

    @property
    def can_be_deleted(self):
        """Verifica se a transação pode ser deletada."""
        if not self.accounting_period:
            return True
        return self.accounting_period.is_open

    @property
    def can_be_reversed(self):
        """Verifica se a transação pode ser estornada."""
        if not self.accounting_period:
            return False
        return not self.accounting_period.is_open and self.transaction_type == 'original'

    @property
    def has_reversal(self):
        """Verifica se esta transação já possui estorno."""
        return self.reversed_by.exists()
