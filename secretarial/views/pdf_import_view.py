from django.views.generic import FormView
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.core.files.base import ContentFile
from secretarial.forms import PDFImportForm
from secretarial.utils.ai_utils import extract_text_from_pdf
from secretarial.models import MinuteProjectModel
from datetime import date
import os


class PDFImportView(PermissionRequiredMixin, FormView):
    """
    View para upload de PDF e extração de texto via OCR usando Mistral.
    """
    permission_required = "secretarial.add_meetingminutemodel"
    template_name = "secretarial/pdf_import.html"
    form_class = PDFImportForm

    def form_valid(self, form):
        """
        Processa o upload do PDF e extrai o texto via OCR.
        """
        pdf_file = form.cleaned_data['pdf_file']

        # Extrair texto do PDF usando OCR
        extracted_text = extract_text_from_pdf(pdf_file)

        # Verificar se houve erro na extração
        if extracted_text.startswith('Erro') or extracted_text.startswith('Chave'):
            messages.error(self.request, extracted_text)
            return redirect('secretarial:pdf-import')

        # Criar projeto de ata com o texto extraído
        minute_project = MinuteProjectModel(
            president=self.request.user if self.request.user.is_pastor else None,
            secretary=self.request.user if self.request.user.is_secretary else None,
            meeting_date=date.today(),
            number_of_attendees='',
            body=extracted_text,
        )
        minute_project.save()

        # Salvar o arquivo PDF temporariamente na sessão
        # Será anexado à ata quando ela for criada
        import base64
        pdf_content = pdf_file.read()
        self.request.session['pdf_attachment'] = {
            'name': pdf_file.name,
            'content': base64.b64encode(pdf_content).decode('utf-8'),  # Converter para base64
            'content_type': pdf_file.content_type,
            'size': len(pdf_content)
        }
        self.request.session['pdf_project_id'] = minute_project.pk

        messages.success(self.request, 'Texto extraído do PDF com sucesso! Você pode editar a ata gerada.')

        # Redirecionar para o formulário de criação de ata com o projeto criado
        return redirect('secretarial:minute-creation-form-view', project_pk=minute_project.pk)

    def form_invalid(self, form):
        """
        Trata formulários inválidos.
        """
        messages.error(self.request, 'Erro no upload do arquivo. Verifique se é um PDF válido.')
        return super().form_invalid(form)