import requests
import base64
import os
from django.conf import settings
from django.core.files.base import ContentFile
try:
    from mistralai import Mistral
    MISTRAL_SDK_AVAILABLE = True
except ImportError:
    MISTRAL_SDK_AVAILABLE = False


def generate_minute_body(prompt):
    if not hasattr(settings, 'MISTRAL_API_KEY') or not settings.MISTRAL_API_KEY:
        return "Chave da API do Mistral não configurada. Configure MISTRAL_API_KEY em settings.py."

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": get_mistral_model_for_task("text"),
        "messages": [
            {
                "role": "user",
                "content": f"Gere o corpo de uma ata de reunião formal para a Igreja Batista Regular de Cidade Satélite baseado apenas na descrição fornecida: {prompt}. Crie um texto narrativo fluido e contínuo, sem divisões excessivas em seções, títulos ou subtítulos. Use parágrafos simples para conectar os eventos de forma natural, adicionando apenas elementos como abertura, decisões ou encerramento se explicitamente mencionados no prompt. Foque estritamente no conteúdo descrito pelo usuário. Formate a saída em HTML puro, usando principalmente <p> para parágrafos, <strong> ou <em> para ênfase, e evite <h1>, <h2>, listas ou quebras desnecessárias. NÃO use blocos de código Markdown como ```html ou ``` – saia apenas com as tags HTML brutas, renderizáveis diretamente em um editor rico como CKEditor."
            }
        ],
        "max_tokens": 5000,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        return f"Erro ao chamar a API do Mistral: {str(e)}"


def extract_text_from_pdf(pdf_file):
    """
    Extrai texto de um arquivo PDF usando a API Mistral OCR.

    Args:
        pdf_file: Arquivo PDF (FileField ou arquivo em memória)

    Returns:
        str: Texto extraído do PDF ou mensagem de erro
    """
    if not hasattr(settings, 'MISTRAL_API_KEY') or not settings.MISTRAL_API_KEY:
        return "Chave da API do Mistral não configurada. Configure MISTRAL_API_KEY em settings.py."

    if not MISTRAL_SDK_AVAILABLE:
        return "SDK Mistral não instalado. Instale com: pip install mistralai"

    try:
        # Inicializar cliente Mistral
        client = Mistral(api_key=settings.MISTRAL_API_KEY)

        # Preparar arquivo para OCR (usa base64 diretamente)
        file_content = pdf_file.read()
        file_name = getattr(pdf_file, 'name', 'uploaded_file.pdf')

        # Converter para base64
        import base64
        pdf_base64 = base64.b64encode(file_content).decode('utf-8')

        # Usar base64 diretamente para OCR (mais simples e confiável)
        ocr_response = client.ocr.process(
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}"
            },
            model="mistral-ocr-latest",
            include_image_base64=False
        )

        # Extrair texto das páginas
        extracted_text = ""
        if hasattr(ocr_response, 'pages') and ocr_response.pages:
            for page in ocr_response.pages:
                if hasattr(page, 'markdown') and page.markdown:
                    extracted_text += page.markdown + "\n\n"

        if not extracted_text.strip():
            return "Não foi possível extrair texto do PDF. Verifique se o arquivo contém texto legível."

        return extracted_text.strip()

    except Exception as e:
        return f"Erro ao processar PDF com OCR: {str(e)}"


def get_mistral_model_for_task(task_type="text"):
    """
    Retorna o modelo Mistral apropriado para o tipo de tarefa.

    Args:
        task_type (str): Tipo de tarefa ("text" para geração de texto, "ocr" para OCR)

    Returns:
        str: Nome do modelo Mistral
    """
    if task_type == "ocr":
        return "mistral-ocr-latest"
    else:
        return getattr(settings, 'MISTRAL_MODEL', 'mistral-small-latest')