from django.views.generic import CreateView
from django.core.files.base import ContentFile
from secretarial.forms import MinuteModelForm
from secretarial.models import (
    MinuteProjectModel, MeetingMinuteModel, MinuteExcerptsModel, MinuteFileModel)
from django.contrib.auth.mixins import PermissionRequiredMixin
import reversion


class MinuteCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "secretarial.add_meetingminutemodel"
    form_class = MinuteModelForm
    template_name = "secretarial/minute_created.html"
    context_object_name = "minute"
    model = MeetingMinuteModel

    # Tirei, parece inútil, não tem url pattern para pegar PK... Vou ter um tempo..
    """ def get_initial(self):
        initial = super().get_initial()

        if self.kwargs.get("pk"):
            minute_data = MinuteProjectModel.objects.get(
                pk=self.kwargs.get("pk"))
            print(minute_data)
            initial["president"] = minute_data.president
            initial["secretary"] = minute_data.secretary
            initial["meeting_date"] = minute_data.meeting_date.isoformat()
            initial["number_of_attendees"] = minute_data.number_of_atendees
            initial["body"] = minute_data.body
            initial["agenda"] = minute_data.meeting_agenda.all()
        return initial """

    def form_valid(self, form):
        """
        Salva a ata e verifica se há um PDF para anexar.
        """
        # Salvar a ata primeiro com controle de versão
        with reversion.create_revision():
            reversion.set_user(self.request.user)
            response = super().form_valid(form)

        # Verificar se há um PDF na sessão para anexar
        pdf_attachment = self.request.session.get('pdf_attachment')
        if pdf_attachment:
            try:
                # Decodificar o conteúdo base64 de volta para bytes
                import base64
                pdf_content = base64.b64decode(pdf_attachment['content'])
                # Criar o arquivo a partir do conteúdo armazenado
                pdf_file = ContentFile(pdf_content, name=pdf_attachment['name'])

                # Criar o anexo
                MinuteFileModel.objects.create(
                    minute=self.object,
                    file=pdf_file,
                    description=f"PDF importado - {pdf_attachment['name']}"
                )

                # Limpar a sessão
                del self.request.session['pdf_attachment']
                if 'pdf_project_id' in self.request.session:
                    del self.request.session['pdf_project_id']

            except Exception as e:
                # Log do erro, mas não falhar a criação da ata
                print(f"Erro ao anexar PDF: {e}")

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        print("Contexto: ", self)

        context["excerpts_list"] = MinuteExcerptsModel.objects.all().order_by(
            "-times_used")

        return context
