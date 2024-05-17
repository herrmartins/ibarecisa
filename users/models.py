from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.db import transaction
from users.utils.user_profile_path import user_profile_image_path
from django_resized import ResizedImageField


class CustomUser(AbstractUser):
    profile_image = ResizedImageField(
        size=[200, 200], upload_to=user_profile_image_path, blank=True, null=True
    )
    date_of_birth = models.DateField(
        blank=True, null=True, auto_now=False, auto_now_add=False
    )
    address = models.CharField(blank=True, max_length=255)
    email = models.EmailField(blank=False, null=False)
    # Não há validação, a não ser do próprio phonefield
    # Se colocar uma validação de telefone brasileiro,
    # se for estrangeiro, não vai dar.
    # Como, a princípio, não serão milhares de usuários,
    # vai dar certo.
    phone_number = PhoneNumberField(
        blank=True, unique=True, region="BR", null=True)
    is_whatsapp = models.BooleanField(blank=True, default=False)
    about = models.TextField(blank=True)
    married_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="spouse"
    )
    date_of_marriage = models.DateField(
        blank=True, null=True, auto_now=False, auto_now_add=False
    )
    is_pastor = models.BooleanField(blank=True, default=False)
    is_secretary = models.BooleanField(blank=True, default=False)
    is_treasurer = models.BooleanField(blank=True, default=False)

    class Types(models.TextChoices):
        # Um membro
        REGULAR = "REGULAR", "Membro"
        # Um membro com alguma função que utilize o sistema além do comum
        STAFF = "EQUIPE", "Equipe"
        # Caso se contrate um tesoureiro não membro
        ONLY_WORKER = "TRABALHADOR", "Contratado"

        CONGREGATED = "CONGREGADO", "Congregado"

        SIMPLE_USER = "USUARIO", "Usuário"

    type = models.CharField(
        _("Type"), max_length=50, choices=Types.choices, default=Types.SIMPLE_USER
    )

    def get_absolute_url(self):
        return reverse_lazy(
            "users:user-profile", kwargs={"pk": str(self.id)}, current_app="users"
        )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        try:
            this = CustomUser.objects.get(id=self.id)
            if this.profile_image != self.profile_image:
                this.profile_image.delete(save=False)
        except CustomUser.DoesNotExist:
            pass
        super(CustomUser, self).save(*args, **kwargs)


@receiver(post_save, sender=CustomUser)
def set_initial_user_type(sender, instance, created, **kwargs):
    # Retrieve or create necessary groups
    regular_group, _ = Group.objects.get_or_create(name="members")
    secretarial_group, _ = Group.objects.get_or_create(name="secretary")
    treasury_group, _ = Group.objects.get_or_create(name="treasurer")
    pastor_group, _ = Group.objects.get_or_create(name="pastor")
    users_group, _ = Group.objects.get_or_create(name="users")

    instance.groups.clear()
    has_any_function = (
        instance.is_pastor or instance.is_secretary or instance.is_treasurer
    )
    if not has_any_function and not (
        instance.type
        in [
            CustomUser.Types.CONGREGATED,
            CustomUser.Types.SIMPLE_USER,
        ]
    ):
        instance.type = CustomUser.Types.REGULAR
    elif has_any_function and not (
        instance.type
        in [
            CustomUser.Types.CONGREGATED,
            CustomUser.Types.SIMPLE_USER,
        ]
    ):
        instance.type = CustomUser.Types.STAFF

    if instance.is_superuser:
        return
    else:
        if instance.type in [
            CustomUser.Types.CONGREGATED,
            CustomUser.Types.SIMPLE_USER,
        ]:
            instance.error_message = "Congregado não pode ter funções..."
            instance.is_pastor = False
            instance.is_secretary = False
            instance.is_treasurer = False
            instance.groups.clear()
            instance.groups.add(users_group)
        else:
            if instance.type == CustomUser.Types.REGULAR:
                instance.groups.add(regular_group)
            elif instance.is_pastor:
                if instance.is_secretary and instance.is_treasurer:
                    instance.groups.add(
                        pastor_group, secretarial_group, treasury_group)
                elif instance.is_secretary:
                    instance.groups.add(pastor_group, secretarial_group)
                elif instance.is_treasurer:
                    instance.groups.add(pastor_group, treasury_group)
                else:
                    instance.groups.add(pastor_group)
                instance.type = CustomUser.Types.STAFF
            elif instance.is_secretary:
                if instance.is_treasurer:
                    instance.groups.add(secretarial_group, treasury_group)
                else:
                    instance.groups.add(secretarial_group)
                instance.type = CustomUser.Types.STAFF
            elif instance.is_treasurer:
                instance.groups.add(treasury_group)
                instance.type = CustomUser.Types.STAFF

        if instance.type == CustomUser.Types.STAFF:
            instance.is_staff = True
        else:
            instance.is_staff = False

    user_groups = instance.groups.all()

    with transaction.atomic():
        # Disable the post_save signal temporarily while saving
        post_save.disconnect(set_initial_user_type, sender=CustomUser)
        instance.save()
        # Reconnect the signal after saving
        post_save.connect(set_initial_user_type, sender=CustomUser)
