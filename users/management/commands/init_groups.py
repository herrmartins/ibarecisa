from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create permission groups and assigns permissions to them"

    def handle(self, *args, **options):
        treasurer_permissions = [
            "secretarial.view_meetingminutemodel",
            "treasury.add_categorymodel",
            "treasury.change_categorymodel",
            "treasury.delete_categorymodel",
            "treasury.view_categorymodel",
            "treasury.add_monthlybalance",
            "treasury.change_monthlybalance",
            "treasury.delete_monthlybalance",
            "treasury.view_monthlybalance",
            "treasury.add_monthlyreportmodel",
            "treasury.change_monthlyreportmodel",
            "treasury.delete_monthlyreportmodel",
            "treasury.view_monthlyreportmodel",
            "treasury.add_monthlytransactionbycategorymodel",
            "treasury.change_monthlytransactionbycategorymodel",
            "treasury.delete_monthlytransactionbycategorymodel",
            "treasury.view_monthlytransactionbycategorymodel",
            "treasury.add_transactionedithistory",
            "treasury.change_transactionedithistory",
            "treasury.delete_transactionedithistory",
            "treasury.view_transactionedithistory",
            "treasury.add_transactionmodel",
            "treasury.change_transactionmodel",
            "treasury.delete_transactionmodel",
            "treasury.view_transactionmodel",
            "secretarial.view_meetingminutemodel",
        ]
        secretarial_permissions = [
            "auth.add_permission",
            "auth.change_permission",
            "auth.delete_permission",
            "auth.view_permission",
            "secretarial.add_meetingagendamodel",
            "secretarial.change_meetingagendamodel",
            "secretarial.delete_meetingagendamodel",
            "secretarial.view_meetingagendamodel",
            "secretarial.add_meetingminutemodel",
            "secretarial.change_meetingminutemodel",
            "secretarial.delete_meetingminutemodel",
            "secretarial.view_meetingminutemodel",
            "secretarial.add_minuteexcerptsmodel",
            "secretarial.change_minuteexcerptsmodel",
            "secretarial.delete_minuteexcerptsmodel",
            "secretarial.view_minuteexcerptsmodel",
            "secretarial.add_minutefilemodel",
            "secretarial.change_minutefilemodel",
            "secretarial.delete_minutefilemodel",
            "secretarial.view_minutefilemodel",
            "secretarial.add_minuteprojectmodel",
            "secretarial.change_minuteprojectmodel",
            "secretarial.delete_minuteprojectmodel",
            "secretarial.view_minuteprojectmodel",
            "secretarial.add_minutetemplatemodel",
            "secretarial.change_minutetemplatemodel",
            "secretarial.delete_minutetemplatemodel",
            "secretarial.view_minutetemplatemodel",
            "users.add_customuser",
            "users.change_customuser",
            "users.delete_customuser",
            "users.view_customuser",
            "treasury.view_monthlybalance",
            "treasury.view_transactionmodel",
            "treasury.view_monthlyreportmodel",
            "treasury.view_monthlytransactionbycategorymodel",
            "treasury.add_monthlybalance",
        ]

        pastor_permissions = secretarial_permissions + treasurer_permissions

        members_permissions = [
            "secretarial.view_meetingminutemodel",
            "secretarial.view_minutefilemodel",
            "treasury.view_monthlybalance",
            "treasury.view_categorymodel",
            "treasury.view_monthlyreportmodel",
            "treasury.view_monthlytransactionbycategorymodel",
            "treasury.view_transactionmodel",
        ]

        treasurer_group, created_treasurer = Group.objects.get_or_create(
            name="treasurer"
        )
        secretarial_group, created_secretarial = Group.objects.get_or_create(
            name="secretary"
        )
        pastor_group, created_pastor = Group.objects.get_or_create(name="pastor")
        members_group, created_members = Group.objects.get_or_create(name="members")
        congregated_group, created_congregated = Group.objects.get_or_create(
            name="congregated"
        )
        users_group, created_users = Group.objects.get_or_create(name="users")

        # Sempre atualizar permissões (não apenas na criação)
        add_permissions_to_group(treasurer_group, treasurer_permissions)
        add_permissions_to_group(secretarial_group, secretarial_permissions)
        add_permissions_to_group(pastor_group, pastor_permissions)
        add_permissions_to_group(members_group, members_permissions)


def add_permissions_to_group(group, permission_strings):
    # Limpar permissões existentes para garantir estado consistente
    group.permissions.clear()

    for perm_string in permission_strings:
        app_label, codename = perm_string.split(".")
        permission = Permission.objects.get(
            codename=codename, content_type__app_label=app_label
        )
        group.permissions.add(permission)
