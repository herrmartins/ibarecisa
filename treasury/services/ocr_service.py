"""
Serviço de OCR para extração de dados de comprovantes.

Em desenvolvimento (DEBUG=True): Usa Ollama com DeepSeek-OCR
Em produção (DEBUG=False): Usa Mistral OCR
"""

import base64
import io
import json
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Optional, Dict, Any

import requests
from django.conf import settings
from PIL import Image
from pdf2image import convert_from_bytes

try:
    from mistralai import Mistral
    MISTRAL_SDK_AVAILABLE = True
except ImportError:
    MISTRAL_SDK_AVAILABLE = False

from treasury.models import CategoryModel


class ReceiptOCRService:
    """Serviço para extrair dados de comprovantes usando OCR/LLM."""

    def __init__(self):
        self.debug_mode = getattr(settings, 'DEBUG', False)
        # Forçar Mistral mesmo em dev (para testes)
        self.force_mistral = getattr(settings, 'USE_MISTRAL_OCR', False)

    def extract_from_receipt(self, image_file) -> Dict[str, Any]:
        """
        Extrai dados de um comprovante de pagamento.

        Args:
            image_file: Arquivo de imagem (JPEG, PNG, PDF)

        Returns:
            Dict com: description, amount, date, category_id, is_positive, confidence
        """
        # Ler arquivo
        file_content = image_file.read()
        file_name = getattr(image_file, 'name', 'receipt.jpg')

        # Detectar tipo de arquivo
        is_pdf = file_name.lower().endswith('.pdf')

        if is_pdf:
            # Converter PDF para imagem
            try:
                images = convert_from_bytes(file_content, dpi=200, fmt='png')
                if not images:
                    return {
                        'error': 'PDF vazio ou não foi possível converter.',
                        'description': '',
                        'amount': None,
                        'date': None,
                        'category_name': None,
                        'category_id': None,
                        'is_positive': True,
                        'confidence': 0,
                    }
                # Usar primeira página
                img = images[0]
            except Exception as e:
                return {
                    'error': f'Erro ao converter PDF: {str(e)}',
                    'description': '',
                    'amount': None,
                    'date': None,
                    'category_name': None,
                    'category_id': None,
                    'is_positive': True,
                    'confidence': 0,
                }
        else:
            # Abrir imagem diretamente
            try:
                img = Image.open(io.BytesIO(file_content))
            except Exception as e:
                return {
                    'error': f'Erro ao ler imagem: {str(e)}',
                    'description': '',
                    'amount': None,
                    'date': None,
                    'category_name': None,
                    'category_id': None,
                    'is_positive': True,
                    'confidence': 0,
                }

        # Validar tamanho da imagem (mínimo 50x50 pixels para qwen3-vl)
        width, height = img.size
        if width < 50 or height < 50:
            return {
                'error': f'Imagem muito pequena ({width}x{height}). Mínimo: 50x50 pixels.',
                'description': '',
                'amount': None,
                'date': None,
                'category_name': None,
                'category_id': None,
                'is_positive': True,
                'confidence': 0,
            }

        # Converter para PNG e depois base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        file_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')

        print(f"[OCR] Imagem convertida: {width}x{height}, tamanho base64: {len(file_base64)} chars")

        # Debug: salvar imagem temporária para inspeção
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            print(f"[OCR] Imagem salva em: {f.name}")

        # Buscar categorias disponíveis
        categories = list(CategoryModel.objects.values_list('name', flat=True))

        # Chamar OCR apropriado
        # Produção (DEBUG=False): SEMPRE Mistral
        # Desenvolvimento (DEBUG=True): Ollama, a menos que USE_MISTRAL_OCR=True
        use_mistral = (not self.debug_mode) or self.force_mistral

        if use_mistral:
            result = self._extract_with_mistral(file_base64, 'image/png', categories)
        else:
            result = self._extract_with_ollama(file_base64, 'image/png', categories)

        return result

    def _extract_with_ollama(self, file_base64: str, file_type: str, categories: list) -> Dict[str, Any]:
        """
        Extrai dados usando Ollama com qwen2-vl ou qwen3-vl (modelo multimodal).

        Usa a API HTTP do Ollama para processar a imagem.

        Args:
            file_base64: Arquivo em base64
            file_type: Tipo MIME do arquivo
            categories: Lista de categorias disponíveis

        Returns:
            Dict com os dados extraídos
        """
        ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
        ollama_model = getattr(settings, 'OLLAMA_OCR_MODEL', 'qwen3-vl:8b')

        # Prompt melhorado para extração estruturada
        categories_formatted = "\n".join([f"- {cat}" for cat in categories]) if categories else "- Outros"

        prompt = f"""Extraia as informações deste comprovante de pagamento e retorne APENAS no formato JSON especificado.

            Categorias disponíveis:
            {categories_formatted}

            Retorne EXATAMENTE este JSON (substitua os valores):
            {{
            "description": "Nome da Loja - tipo de produtos (quantidade itens)",
            "amount": 0.00,
            "date": "2026-01-15",
            "category": "nome da categoria",
            "is_positive": false,
            "confidence": 80
            }}

            Regras:
            - description: Formato "Loja - tipo de itens (X itens)" ou apenas nome da loja
            - amount: Valor TOTAL em decimal (ex: 123.45)
            - date: Data no formato YYYY-MM-DD
            - category: Escolha UMA categoria da lista acima
            - is_positive: false (comprovantes são despesas)
            - confidence: 0-100 baseado na clareza da imagem

            Retorne APENAS o JSON, sem texto adicional."""

        try:
            print(f"[OCR] Enviando para Ollama (modelo: {ollama_model})...")
            print(f"[OCR] Tamanho do base64: {len(file_base64)} chars")

            # Usar API HTTP do Ollama
            payload = {
                'model': ollama_model,
                'prompt': prompt,
                'images': [file_base64],
                'stream': False
            }

            response = requests.post(
                f'{ollama_host}/api/generate',
                json=payload,
                timeout=360
            )
            print(f"[OCR] Status code: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            print(f"[OCR] JSON completo recebido: {json.dumps(result, indent=2)}...")

            ocr_text = result.get('response', '')

            print(f"[OCR] Resposta recebida ({len(ocr_text)} chars):")
            print(f"[OCR] {ocr_text[:500]}...")

            # Tentar parsear JSON da resposta
            extracted = self._parse_fallback_json(ocr_text)
            if not extracted:
                # Se falhou, tentar parsing de texto livre
                extracted = self._parse_receipt_text(ocr_text, categories)

            extracted['raw_text'] = ocr_text

            print(f"[OCR] Dados extraídos:")
            for key, value in extracted.items():
                if key != 'raw_text':
                    print(f"[OCR]   {key}: {value}")

            normalized = self._normalize_extracted_data(extracted, categories)
            return normalized

        except Exception as e:
            print(f"[OCR] Erro: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': f'Erro ao comunicar com Ollama: {str(e)}',
                'description': '',
                'amount': None,
                'date': None,
                'category_name': None,
                'category_id': None,
                'is_positive': True,
                'confidence': 0,
            }

    def extract_multiple_from_receipt(self, image_file) -> Dict[str, Any]:
        """
        Extrai múltiplas transações de uma imagem (lista, envelopes, urna, etc).

        Args:
            image_file: Arquivo de imagem (JPEG, PNG, PDF)

        Returns:
            Dict com: transactions (array), error (opcional)
        """
        # Ler arquivo
        file_content = image_file.read()
        file_name = getattr(image_file, 'name', 'receipt.jpg')

        # Detectar tipo de arquivo
        is_pdf = file_name.lower().endswith('.pdf')

        if is_pdf:
            # Converter PDF para imagem
            try:
                images = convert_from_bytes(file_content, dpi=200, fmt='png')
                if not images:
                    return {
                        'error': 'PDF vazio ou não foi possível converter.',
                        'transactions': []
                    }
                img = images[0]
            except Exception as e:
                return {
                    'error': f'Erro ao converter PDF: {str(e)}',
                    'transactions': []
                }
        else:
            try:
                img = Image.open(io.BytesIO(file_content))
            except Exception as e:
                return {
                    'error': f'Erro ao ler imagem: {str(e)}',
                    'transactions': []
                }

        # Validar tamanho
        width, height = img.size
        if width < 50 or height < 50:
            return {
                'error': f'Imagem muito pequena ({width}x{height}).',
                'transactions': []
            }

        # Converter para PNG e depois base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        file_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')

        # Buscar categorias
        categories = list(CategoryModel.objects.values_list('name', flat=True))

        # Chamar OCR múltiplo
        # Produção (DEBUG=False): SEMPRE Mistral
        # Desenvolvimento (DEBUG=True): Ollama, a menos que USE_MISTRAL_OCR=True
        use_mistral = (not self.debug_mode) or self.force_mistral

        if use_mistral:
            return self._extract_multiple_with_mistral(file_base64, 'image/png', categories)
        else:
            return self._extract_multiple_with_ollama(file_base64, 'image/png', categories)

    def _extract_multiple_with_ollama(self, file_base64: str, file_type: str, categories: list) -> Dict[str, Any]:
        """
        Extrai múltiplas transações usando Ollama.

        Args:
            file_base64: Arquivo em base64
            file_type: Tipo MIME do arquivo
            categories: Lista de categorias disponíveis

        Returns:
            Dict com: transactions (array), error (opcional)
        """
        ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
        ollama_model = getattr(settings, 'OLLAMA_OCR_MODEL', 'qwen3-vl:8b')

        categories_formatted = "\n".join([f"- {cat}" for cat in categories]) if categories else "- Outros"

        prompt = f"""Analise esta imagem e retorne APENAS um array JSON com todas as transações.

Categorias: {categories_formatted}

Formato OBRIGATÓRIO (retorne EXATAMENTE isto):
[
  {{"description": "Envelope 895 - Dízimo", "amount": 2.50, "date": "2026-02-02", "category": "Dízimos", "is_positive": true, "confidence": 90}},
  {{"description": "Envelope 895 - Missões", "amount": 50.00, "date": "2026-02-02", "category": "Missões", "is_positive": true, "confidence": 90}},
  {{"description": "Envelope 895 - Urna", "amount": 60.00, "date": "2026-02-02", "category": "Ofertas", "is_positive": true, "confidence": 90}}
]

Regras:
- NÃO explique, NÃO use tabelas, NÃO use markdown
- Retorne APENAS o array JSON entre colchetes
- description: "Envelope X - Categoria" ou "Nome - Categoria"
- amount: número decimal (ex: 2.50)
- date: YYYY-MM-DD (ou data de hoje: {datetime.now().strftime('%Y-%m-%d')})
- category: use exatamente o nome da categoria da lista
- is_positive: SEMPRE true para dízimos, ofertas, envelope, urna, contribuições. Use false APENAS para despesas/notas de compra.
- confidence: 70 a 90

COMECE O JSON COM [ e TERMINA COM ]"""

        try:
            print(f"[OCR Múltiplo] Enviando para Ollama (modelo: {ollama_model})...")
            print(f"[OCR Múltiplo] Tamanho do base64: {len(file_base64)} chars")

            payload = {
                'model': ollama_model,
                'prompt': prompt,
                'images': [file_base64],
                'stream': False
            }

            response = requests.post(
                f'{ollama_host}/api/generate',
                json=payload,
                timeout=360
            )
            print(f"[OCR Múltiplo] Status code: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            ocr_text = result.get('response', '')

            print(f"[OCR Múltiplo] Resposta recebida ({len(ocr_text)} chars):")
            print(f"[OCR Múltiplo] {ocr_text[:1000]}...")

            # Tentar parsear array JSON
            transactions = self._parse_multiple_json(ocr_text, categories)

            print(f"[OCR Múltiplo] {len(transactions)} transações extraídas")

            return {'transactions': transactions}

        except Exception as e:
            print(f"[OCR Múltiplo] Erro: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': f'Erro ao comunicar com Ollama: {str(e)}',
                'transactions': []
            }

    def _parse_multiple_json(self, text: str, categories: list) -> list:
        """Parseia array JSON de múltiplas transações."""
        # Tentar encontrar array JSON entre ```
        array_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
        if array_match:
            try:
                raw_data = json.loads(array_match.group(1))
                if isinstance(raw_data, list):
                    return [self._normalize_extracted_data(item, categories) for item in raw_data]
            except json.JSONDecodeError:
                pass

        # Tentar encontrar o primeiro [
        start = text.find('[')
        if start != -1:
            # Tentar encontrar o fechamento balanceado
            bracket_count = 0
            for i in range(start, len(text)):
                if text[i] == '[':
                    bracket_count += 1
                elif text[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        try:
                            raw_data = json.loads(text[start:i+1])
                            if isinstance(raw_data, list):
                                return [self._normalize_extracted_data(item, categories) for item in raw_data]
                        except json.JSONDecodeError:
                            pass

        # Se falhou, tentar parsing de texto livre para múltiplas entradas
        return self._parse_multiple_text(text, categories)

    def _parse_multiple_text(self, text: str, categories: list) -> list:
        """Parseia texto livre para extrair múltiplas transações."""
        transactions = []
        lines = text.split('\n')

        current_tx = {
            'description': '',
            'amount': None,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'category': 'Dízimos',
            'is_positive': True,
            'confidence': 60
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Procurar padrões de valor
            amount_match = re.search(r'R?\$\s*([\d.,]+)', line)
            if amount_match:
                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                try:
                    amount = float(amount_str)
                    if amount > 0:
                        # Salvar transação anterior se tiver valor
                        if current_tx['amount']:
                            transactions.append({**current_tx})

                        # Nova transação
                        current_tx = {
                            'description': line[:50],
                            'amount': amount,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'category': 'Dízimos',
                            'is_positive': True,
                            'confidence': 50
                        }
                except ValueError:
                    pass

        # Adicionar última transação
        if current_tx['amount']:
            transactions.append(current_tx)

        return [self._normalize_extracted_data(tx, categories) for tx in transactions]

    def _extract_multiple_with_mistral(self, file_base64: str, file_type: str, categories: list) -> Dict[str, Any]:
        """
        Extrai múltiplas transações usando Mistral OCR (produção).
        """
        if not MISTRAL_SDK_AVAILABLE:
            return {
                'error': 'SDK Mistral não instalado.',
                'transactions': []
            }

        if not hasattr(settings, 'MISTRAL_API_KEY') or not settings.MISTRAL_API_KEY:
            return {
                'error': 'MISTRAL_API_KEY não configurado',
                'transactions': []
            }

        client = Mistral(api_key=settings.MISTRAL_API_KEY)

        # Prompt para múltiplas transações
        categories_formatted = ", ".join(categories)

        prompt = f"""Extraia TODAS as transações desta imagem de envelopes/lista.

Categorias disponíveis: {categories_formatted}

Retorne APENAS este array JSON:
[
  {{"description": "Envelope X - Categoria", "amount": 100.00, "date": "2026-02-02", "category": "Dízimos", "is_positive": true, "confidence": 90}}
]

Regras:
- Cada envelope com múltiplas categorias = múltiplas transações
- is_positive: SEMPRE true para envelopes/dízimos/ofertas. Use false APENAS para despesas.
- amount: número decimal
- date: YYYY-MM-DD ou data de hoje
- Retorne APENAS o array JSON"""

        try:
            # Usar OCR do Mistral
            ocr_response = client.ocr.process(
                document={
                    "type": "image_url",
                    "image_url": f"data:{file_type};base64,{file_base64}"
                },
                model="mistral-ocr-latest"
            )

            # Extrair texto do OCR
            ocr_text = ""
            if hasattr(ocr_response, 'pages') and ocr_response.pages:
                for page in ocr_response.pages:
                    if hasattr(page, 'markdown') and page.markdown:
                        ocr_text += page.markdown + "\n"
            elif hasattr(ocr_response, 'markdown'):
                ocr_text = ocr_response.markdown

            # Usar modelo para extrair array JSON
            model = getattr(settings, 'MISTRAL_MODEL', 'mistral-small-latest')

            chat_response = client.chat.complete(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um assistente especializado em extrair dados de listas de transações. Responda APENAS com um array JSON válido, sem qualquer texto adicional."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nTexto extraído:\n{ocr_text}"
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.1
            )

            response_text = chat_response.choices[0].message.content
            print(f"[OCR Múltiplo Mistral] Resposta: {response_text[:500]}...")

            # A resposta pode ter um wrapper, tentar extrair o array
            result = json.loads(response_text)

            # Se result for um objeto com uma propriedade array, extrair
            if isinstance(result, dict):
                for key in ['transactions', 'data', 'results', 'items']:
                    if key in result and isinstance(result[key], list):
                        result = result[key]
                        break

            if not isinstance(result, list):
                # Tentar parsear o texto para encontrar array
                transactions = self._parse_multiple_json(response_text, categories)
            else:
                transactions = [self._normalize_extracted_data(tx, categories) for tx in result]

            return {'transactions': transactions}

        except Exception as e:
            print(f"[OCR Múltiplo Mistral] Erro: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': f'Erro ao processar com Mistral: {str(e)}',
                'transactions': []
            }

    def _extract_with_mistral(self, file_base64: str, file_type: str, categories: list) -> Dict[str, Any]:
        """
        Extrai dados usando Mistral OCR (produção).

        Args:
            file_base64: Arquivo em base64
            file_type: Tipo MIME do arquivo
            categories: Lista de categorias disponíveis

        Returns:
            Dict com os dados extraídos
        """
        if not MISTRAL_SDK_AVAILABLE:
            raise Exception('SDK Mistral não instalado. Instale com: pip install mistralai')

        if not hasattr(settings, 'MISTRAL_API_KEY') or not settings.MISTRAL_API_KEY:
            raise Exception('MISTRAL_API_KEY não configurado')

        client = Mistral(api_key=settings.MISTRAL_API_KEY)
        prompt = self._build_extraction_prompt(categories)

        try:
            # Usar OCR do Mistral
            ocr_response = client.ocr.process(
                document={
                    "type": "image_url",
                    "image_url": f"data:{file_type};base64,{file_base64}"
                },
                model="mistral-ocr-latest"
            )

            # Extrair texto do OCR
            ocr_text = ""
            if hasattr(ocr_response, 'pages') and ocr_response.pages:
                for page in ocr_response.pages:
                    if hasattr(page, 'markdown') and page.markdown:
                        ocr_text += page.markdown + "\n"
            elif hasattr(ocr_response, 'markdown'):
                ocr_text = ocr_response.markdown

            # Agora usar o modelo de texto para extrair dados estruturados
            model = getattr(settings, 'MISTRAL_MODEL', 'mistral-small-latest')

            chat_response = client.chat.complete(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um assistente especializado em extrair dados de comprovantes de pagamento. Responda APENAS com um JSON válido, sem qualquer texto adicional."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nTexto do comprovante:\n{ocr_text}"
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.1
            )

            response_text = chat_response.choices[0].message.content
            extracted = json.loads(response_text)

            return self._normalize_extracted_data(extracted, categories)

        except Exception as e:
            return {
                'error': f'Erro ao processar com Mistral: {str(e)}',
                'description': '',
                'amount': None,
                'date': None,
                'category_name': None,
                'category_id': None,
                'is_positive': True,
                'confidence': 0,
            }

    def _build_extraction_prompt(self, categories: list) -> str:
        """Constrói o prompt para extração de dados."""
        # Formatar categorias como lista numerada para ficar mais claro
        categories_formatted = "\n".join([f"- {cat}" for cat in categories]) if categories else "- Outros"

        return f"""Extraia informações deste comprovante e retorne JSON:

Categorias disponíveis:
{categories_formatted}

Instruções:
- description: Formato: "Nome da Loja - tipo de produtos comprados (X itens)"
  * Exemplo: "Leroy Merlin - materiais elétricos (10 itens)"
  * Exemplo: "Mercado Extra - alimentos e produtos de limpeza (5 itens)"
  * Se não identificar os itens, use apenas o nome da loja
- amount: Valor TOTAL a pagar (número decimal com ponto)
- date: Data no formato YYYY-MM-DD
- category: Escolha UMA categoria da lista acima que melhor descreve esta compra
- is_positive: false (comprovantes são despesas)

Retorne APENAS este JSON:
{{
  "description": "Loja - tipo de itens (quantidade itens)",
  "amount": 0.00,
  "date": "2026-01-15",
  "category": "nome exato da categoria da lista",
  "is_positive": false,
  "confidence": 80
}}"""

    def _parse_fallback_json(self, text: str) -> Dict:
        """Tenta extrair JSON de texto mal formatado."""
        # Tentar encontrar JSON entre ```
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Tentar encontrar o primeiro {
        start = text.find('{')
        if start != -1:
            # Tentar encontrar o fechamento balanceado
            brace_count = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        try:
                            return json.loads(text[start:i+1])
                        except json.JSONDecodeError:
                            pass

        # Retornar dict vazio se falhar
        return {}

    def _parse_date(self, date_str: str) -> str:
        """Parseia data de diversos formatos."""
        date_str = date_str.strip()
        # Tentar vários formatos
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return datetime.now().strftime('%Y-%m-%d')

    def _parse_amount(self, amount_str: str) -> float:
        """Parseia valor de diversos formatos brasileiros."""
        amount_str = amount_str.strip()
        # Remover R$, espaços, etc.
        amount_str = re.sub(r'[^\d.,]', '', amount_str)
        # Converter para formato float
        if ',' in amount_str:
            # Tem vírgula como separador decimal (brasileiro)
            amount_str = amount_str.replace('.', '').replace(',', '.')
        else:
            # Sem vírgula, pode ter ponto como decimal
            amount_str = amount_str.replace(',', '')
        try:
            return float(amount_str)
        except ValueError:
            return 0.0

    def _parse_receipt_text(self, text: str, categories: list) -> Dict[str, Any]:
        """Parseia texto extraído do OCR para encontrar dados estruturados."""
        result = {
            'description': '',
            'amount': None,
            'date': None,
            'category': 'Outros',
            'is_positive': False,  # Padrão: comprovante = despesa
            'confidence': 70,
        }

        # Limpar texto
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text).strip()

        print(f"[OCR] Parseando texto ({len(text)} chars): {text}")

        # Tentar extrair do formato estruturado (TOTAL: | DATE: | DESC: |)
        total_match = re.search(r'TOTAL:\s*([^\n]+?)(?=DATE:|DESC:|$)', text, re.IGNORECASE)
        date_match = re.search(r'DATE:\s*([^\n]+?)(?=TOTAL:|DESC:|$)', text, re.IGNORECASE)
        desc_match = re.search(r'DESC:\s*([^\n]+?)(?=TOTAL:|DATE:|$)', text, re.IGNORECASE)

        if date_match or desc_match or total_match:
            # Formato estruturado encontrado
            if date_match:
                date_str = date_match.group(1).strip()
                result['date'] = self._parse_date(date_str)
                print(f"[OCR] Data estruturada: {result['date']}")
            if desc_match:
                result['description'] = desc_match.group(1).strip()
                print(f"[OCR] Descrição estruturada: {result['description']}")
            if total_match:
                amount_str = total_match.group(1).strip()
                result['amount'] = self._parse_amount(amount_str)
                print(f"[OCR] Valor estruturado: {result['amount']}")

            return result

        # Se não achou formato estruturado, tentar parsing livre
        # Extrair valor - procurar TOTAL primeiro, depois outros valores
        amount_patterns = [
            # Padrões específicos NFC-e/Nota Fiscal (valor total no final)
            r'(?:TOTAL\s*(?:GERAL|DA\s*NOTA|A\s*PAGAR)?|VALOR\s*TOTAL|SOMA)\s*R?\$?\s*([\d]{1,3}\.?,?[\d]{3}\.?,?[\d]{1,3},\d{2})',
            r'(?:TOTAL|VALOR\s*TOTAL|VALOR\s*A\s*PAGAR|SOMA)\s*R?\$?\s*([\d]{1,6}[,\.]\d{2})',
            r'(?:TOTAL|VALOR.*?PAGAR)\s*:\s*R?\$?\s*([\d]{1,6}[,\.]\d{2})',
            # Genéricos com R$ (evitar descontos)
            r'R\$\s*([\d]{1,3}\.?,?[\d]{3}\.?,?[\d]{1,3},\d{2})(?!\s*Desc)',
            r'R\$\s*([\d]{1,6}[,\.]\d{2})(?!\s*Desc)',
        ]

        for pattern in amount_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                # Pegar o último match (geralmente o total é o último valor)
                amount_str = matches[-1].group(1) if matches[-1].lastindex else matches[-1].group(0)
                print(f"[OCR] Match encontrado: '{amount_str}' (padrão: {pattern})")

                # Limpar e converter - preservar formato brasileiro
                amount_str = re.sub(r'[^\d.,]', '', amount_str)
                # Para formatos como 1.234,56 ou 1234,56 ou 1.234.56,78
                # Primeiro remover pontos de milhar (antes da vírgula)
                if ',' in amount_str:
                    # Tem vírgula como separador decimal
                    amount_str = amount_str.replace('.', '').replace(',', '.')
                else:
                    # Sem vírgula, pode ser formato com ponto como decimal
                    amount_str = amount_str.replace(',', '')

                try:
                    val = float(amount_str)
                    # Ignorar valores absurdos (> 100000 provavelmente é erro/CNPJ)
                    # Mas também ignorar muito pequenos (< 0.01)
                    if 0.01 <= val < 100000:
                        result['amount'] = val
                        print(f"[OCR] Valor encontrado: {result['amount']}")
                        break
                except ValueError:
                    pass

        # Se não achou TOTAL, tentar somar todos os valores positivos encontrados
        if not result['amount']:
            print(f"[OCR] TOTAL não encontrado, somando valores positivos...")
            # Encontrar todos os valores monetários
            all_values = re.findall(r'-?\s*R?\$?\s*([\d.]+,\d{2})', text)
            total_sum = 0
            for val_str in all_values:
                try:
                    val = float(val_str.replace('.', '').replace(',', '.'))
                    # Somar apenas valores positivos razoáveis (ignorar descontos negativos)
                    if 0.50 < val < 10000:  # Valores razoáveis de item
                        total_sum += val
                        print(f"[OCR]  + {val}")
                except ValueError:
                    pass
            if total_sum > 1:
                result['amount'] = total_sum
                print(f"[OCR] Soma dos valores: {result['amount']}")

        # Extrair data (DD/MM/AAAA, DD-MM-AAAA, etc.)
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/AAAA
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-AAAA
            r'\d{4}/\d{2}/\d{2}',  # AAAA/MM/DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(0)
                # Converter para AAAA-MM-DD
                try:
                    if '/' in date_str:
                        parts = date_str.split('/')
                        if len(parts[0]) == 4:  # AAAA/MM/DD
                            result['date'] = date_str
                        else:  # DD/MM/AAAA
                            result['date'] = f'{parts[2]}-{parts[1]}-{parts[0]}'
                    elif '-' in date_str:
                        parts = date_str.split('-')
                        if len(parts[0]) == 4:  # AAAA-MM-DD
                            result['date'] = date_str
                        else:  # DD-MM-AAAA
                            result['date'] = f'{parts[2]}-{parts[1]}-{parts[0]}'
                    print(f"[OCR] Data encontrada: {result['date']}")
                    break
                except Exception:
                    pass

        # Se não achou data, usar hoje
        if not result['date']:
            result['date'] = datetime.now().strftime('%Y-%m-%d')

        # Extrair descrição - tentar pegar nome do estabelecimento ou informações úteis
        # Dividir por palavras-chave comuns que separam cabeçalho do conteúdo
        split_patterns = [
            r'CNPJ\s*:?',
            r'Documento Auxiliar',
            r'ITEM\s+C\d+',
            r'\*\*Item\*\*\s*\|',
            r'Here\'s extracted',
            r'extracted information',
        ]
        for pattern in split_patterns:
            text_parts = re.split(pattern, text, maxsplit=1, flags=re.IGNORECASE)
            if len(text_parts) > 1:
                text = text_parts[-1]  # Usar a parte após o separador
                break

        # Tentar extrair nome de estabelecimento (geralmente no início)
        # Procurar por padrões como "Conj tom 2pt", "Mercado", etc.
        desc_patterns = [
            # Padrões de produtos/nomes
            r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+)',  # 3+ palavras com maiúscula
            r'(Conj\s+\w+\s+\w+\s+\w+)',  # Conjunto algo
            r'(Mercado\s+\w+)',
            r'(Supermercado\s+\w+)',
        ]

        for pattern in desc_patterns:
            match = re.search(pattern, text)
            if match:
                potential_desc = match.group(1).strip()
                # Usar se for razoável
                if 8 <= len(potential_desc) < 80:
                    result['description'] = potential_desc
                    print(f"[OCR] Descrição encontrada: {result['description']}")
                    break

        # Se não achou descrição adequada, usar padrão
        if not result['description'] or result['description'] == 'Here\'s the extracted':
            result['description'] = 'Compra no estabelecimento'

        return result

    def _infer_category(self, description: str, text: str, categories: list) -> str:
        """Infere a categoria baseada em palavras-chave."""
        # Converter para minúsculas para busca
        desc_lower = description.lower()
        text_lower = text.lower()
        combined = f"{desc_lower} {text_lower}"

        # Mapeamento de palavras-chave para categorias
        keywords_map = {
            # Mercado/Alimentação
            'Mercado': ['mercado', 'supermercado', 'atacadão', 'carrefour', 'wal-mart', 'extra', 'zaffari',
                       'hortifruti', 'açougue', 'padaria', 'farmácia', 'panificadora', 'alimentar'],
            # Construção
            'Construção': ['leroy', 'construção', 'material', 'depósito', 'madeireira', 'lojas cem',
                          'quero-quero', 'c%c', 'sodimaco', 'mm', 'telhanorte',
                          # Materiais elétricos/hidráulicos
                          'tom', 'tomada', '4x2', '2pt', 'pl ceva', 'stella', 'conj', 'conjunto',
                          'elétr', 'cab', 'fio', 'disjunt', 'caixa', 'eletro'],
            # Transporte
            'Transporte': ['uber', '99 taxi', 'taxi', 'posto', 'gasolina', 'combustível', 'estacionamento',
                          'pedágio', 'transporte', 'ônibus', 'metrô'],
            # Alimentação
            'Alimentação': ['restaurante', 'lanchonete', 'fast food', 'mc donalds', 'burger king',
                           'pizza', ' delivery', 'ifood', 'rappi'],
            # Saúde
            'Saúde': ['médico', 'dentista', 'farmácia', 'clínica', 'hospital', 'exame', 'consultório'],
            # Educação
            'Educação': ['escola', 'curso', 'livraria', 'material escolar', 'faculdade'],
            # Lazer
            'Lazer': ['cinema', 'teatro', 'show', 'parque', 'viagem', 'hotel', 'pousada'],
            # Tecnologia
            'Tecnologia': ['net', 'claro', 'vivo', 'tim', 'telefone', 'internet', 'software', 'app'],
            # Vestuário
            'Vestuário': ['roupa', 'calçado', 'loja de roupas', 'cama', 'mesa', 'banho'],
            # Casa
            'Casa': ['móveis', 'eletro', 'eletrodoméstico', 'decoração', 'cama', 'mesa'],
        }

        # Buscar correspondência
        for category, keywords in keywords_map.items():
            for keyword in keywords:
                if keyword.lower() in combined:
                    # Verificar se a categoria existe
                    if category in categories:
                        print(f"[OCR] Categoria inferida: {category} (keyword: {keyword})")
                        return category

        # Se não achou, tentar categoria mais próxima
        for category in categories:
            if category.lower() in combined:
                print(f"[OCR] Categoria encontrada no texto: {category}")
                return category

        print(f"[OCR] Nenhuma categoria inferida, usando 'Outros'")
        return 'Outros'

    def _normalize_extracted_data(self, data: Dict, categories: list) -> Dict[str, Any]:
        """Normaliza e valida os dados extraídos."""
        description = data.get('description', '') or ''

        # Valor
        amount = None
        try:
            raw_amount = data.get('amount', 0)
            if isinstance(raw_amount, str):
                # Remover formatação brasileira
                raw_amount = raw_amount.replace('.', '').replace(',', '.').replace('R$', '').strip()
            amount = float(raw_amount)
        except (ValueError, TypeError, InvalidOperation):
            amount = None

        # Data
        date = data.get('date')
        if date:
            try:
                # Tentar vários formatos
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                    try:
                        parsed_date = datetime.strptime(date, fmt)
                        date = parsed_date.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
                else:
                    date = datetime.now().strftime('%Y-%m-%d')
            except Exception:
                date = datetime.now().strftime('%Y-%m-%d')
        else:
            date = datetime.now().strftime('%Y-%m-%d')

        # Categoria - usar a que veio do JSON se existir no BD
        category_name = data.get('category', 'Outros')

        # Se a categoria do JSON existe no BD, usar ela
        if category_name and category_name in categories:
            print(f"[OCR] Categoria do JSON válida: {category_name}")
        else:
            # Categoria não existe ou é Outros - tentar inferir
            print(f"[OCR] Categoria '{category_name}' não encontrada no BD, tentando inferir...")
            raw_text = data.get('raw_text', '')
            category_name = self._infer_category(description, raw_text, categories)

        # Buscar ID da categoria
        category_id = None
        try:
            category = CategoryModel.objects.filter(name=category_name).first()
            if category:
                category_id = category.id
                print(f"[OCR] Categoria encontrada no BD: {category.name} (id: {category.id})")
            else:
                print(f"[OCR] Categoria '{category_name}' não existe no BD, deixando como None")
        except Exception as e:
            print(f"[OCR] Erro ao buscar categoria: {e}")
            pass

        # is_positive
        is_positive = data.get('is_positive', True)

        # Confidence
        confidence = data.get('confidence', 50)
        if isinstance(confidence, str):
            try:
                confidence = int(confidence)
            except ValueError:
                confidence = 50

        return {
            'description': description,
            'amount': amount,
            'date': date,
            'category_name': category_name,
            'category_id': category_id,
            'is_positive': is_positive,
            'confidence': min(max(confidence, 0), 100),
            'raw_data': data,  # Para debug
        }
