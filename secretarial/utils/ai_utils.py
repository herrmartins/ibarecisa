import requests
from django.conf import settings


def generate_minute_body(prompt):
    if not hasattr(settings, 'MISTRAL_API_KEY') or not settings.MISTRAL_API_KEY:
        return "Chave da API do Mistral não configurada. Configure MISTRAL_API_KEY em settings.py."

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {
                "role": "user",
                "content": f"Gere uma ata de reunião formal para a Igreja Batista Regular de Cidade Satélite baseada na descrição fornecida: {prompt}. Inclua estrutura padrão de ata de igreja, com abertura (data, presidente, secretário, número de presentes), leitura da ata anterior se aplicável, relatório financeiro se mencionado, assuntos discutidos (agenda), decisões tomadas, e encerramento com aprovações, quando houver. Se houver só relatórios, ignore o resto, coloque só os relatórios, além do cabeçalho e fim padrão. Formate a saída em HTML puro, usando tags como <h1> ou <h2> para títulos, <p> para parágrafos, <ul> ou <ol> para listas de itens, <strong> para ênfase, e evite Markdown ou formatação de texto simples. O conteúdo deve ser renderizável diretamente em um editor rico como CKEditor."
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