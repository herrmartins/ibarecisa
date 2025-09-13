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
        "model": "mistral-small-latest",
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