from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from datetime import date
from secretarial.forms import MinuteProjectModelForm
from secretarial.models import (
    MeetingMinuteModel,
    MinuteProjectModel,
    MinuteExcerptsModel,
    MinuteTemplateModel,
)
from secretarial.utils.ai_utils import generate_minute_body
from django.contrib.auth.mixins import PermissionRequiredMixin


class MinuteHomeView(PermissionRequiredMixin, TemplateView):
    permission_required = "secretarial.view_meetingminutemodel"
    template_name = "secretarial/minute_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        minutes = MeetingMinuteModel.objects.all()

        context["meeting_minutes"] = MeetingMinuteModel.objects.all().reverse()[:10]
        context["number_of_projects"] = MinuteProjectModel.objects.count()
        context["number_of_excerpts"] = MinuteExcerptsModel.objects.count()
        context["number_of_minutes"] = minutes.count()
        context["minutes"] = minutes
        context["number_of_templates"] = MinuteTemplateModel.objects.count()
        context["templates"] = MinuteTemplateModel.objects.all()

        return context

    def post(self, request, *args, **kwargs):
        prompt = request.POST.get('prompt', '').strip()
        template_id = request.POST.get('template', '').strip()
        if not prompt:
            messages.error(request, 'Por favor, forneça uma descrição para a ata.')
            return redirect('secretarial:minute-home')

        if template_id:
            try:
                template = MinuteTemplateModel.objects.get(pk=template_id)
                prompt = f"Use este modelo como base: {template.body}\n\n{prompt}"
            except MinuteTemplateModel.DoesNotExist:
                pass  # Ignore if template not found

        body = generate_minute_body(prompt)
        if body.startswith('Erro') or body.startswith('Chave'):
            messages.error(request, body)
            return redirect('secretarial:minute-home')

        minute_project = MinuteProjectModel(
            president=request.user if request.user.is_pastor else None,
            secretary=request.user if request.user.is_secretary else None,
            meeting_date=date.today(),
            number_of_attendees='',
            body=body,
        )
        minute_project.save()

        messages.success(request, 'Projeto de ata criado com sucesso usando IA!')
        return redirect('secretarial:list-minutes-projects')
