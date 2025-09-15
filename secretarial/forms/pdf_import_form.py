from django import forms
from django.core.exceptions import ValidationError


class PDFImportForm(forms.Form):
    """
    Formulário para upload de arquivo PDF para extração de texto via OCR.
    """
    pdf_file = forms.FileField(
        label="Arquivo PDF",
        help_text="Selecione um arquivo PDF para extrair o texto",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        })
    )

    def clean_pdf_file(self):
        """
        Valida o arquivo PDF enviado.
        """
        pdf_file = self.cleaned_data.get('pdf_file')

        if not pdf_file:
            raise ValidationError("Por favor, selecione um arquivo PDF.")

        # Verificar extensão do arquivo
        if not pdf_file.name.lower().endswith('.pdf'):
            raise ValidationError("Apenas arquivos PDF são permitidos.")

        # Verificar tamanho do arquivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB em bytes
        if pdf_file.size > max_size:
            raise ValidationError("O arquivo deve ter no máximo 10MB.")

        # Verificar tipo MIME
        if pdf_file.content_type != 'application/pdf':
            raise ValidationError("O arquivo deve ser um PDF válido.")

        return pdf_file