"""
Serviço de OCR para extração de dados de comprovantes.

Em desenvolvimento (DEBUG=True): Usa Ollama com DeepSeek-OCR
Em produção (DEBUG=False): Usa Mistral OCR
"""

import base64
import io
import json
import logging
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Optional, Dict, Any

import requests
from django.conf import settings
from PIL import Image
from pdf2image import convert_from_bytes
import pypdf

logger = logging.getLogger(__name__)

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

    @property
    def ocr_timeout(self) -> int:
        return 360 if self.debug_mode else 60

    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extrai texto selecionável de um PDF usando pypdf."""
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_content))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
            return "\n".join(text_parts)
        except Exception as e:
            logger.warning(f"Erro ao extrair texto do PDF com pypdf: {e}")
            return ""

    def _prepare_pdf_for_vision(self, file_content: bytes) -> tuple:
        """
        Converte todas as páginas de PDF em uma única imagem combinada.
        Retorna (base64_string, page_count) ou (None, 0).
        """
        try:
            images = convert_from_bytes(file_content, dpi=200, fmt='png')
            if not images:
                return None, 0

            if len(images) == 1:
                img = images[0]
            else:
                max_width = max(i.width for i in images)
                total_height = sum(i.height for i in images)
                combined = Image.new('RGB', (max_width, total_height), 'white')
                y_offset = 0
                for page_img in images:
                    combined.paste(page_img, (0, y_offset))
                    y_offset += page_img.height
                img = combined

            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode('utf-8'), len(images)
        except Exception as e:
            logger.error(f"Erro ao converter PDF para imagem: {e}")
            return None, 0

    def _is_pdf_text_sufficient(self, text: str) -> bool:
        """Verifica se o texto extraído do PDF é suficiente para extração."""
        return len(text.strip()) >= 50

    def extract_from_receipt(self, image_file) -> Dict[str, Any]:
        """
        Extrai dados de um comprovante de pagamento.

        Args:
            image_file: Arquivo de imagem (JPEG, PNG, PDF)

        Returns:
            Dict com: description, amount, date, category_id, is_positive, confidence
        """
        file_name = getattr(image_file, 'name', 'receipt.jpg')
        content_type = getattr(image_file, 'content_type', '').lower()

        is_pdf = (file_name.lower().endswith('.pdf') or
                   content_type == 'application/pdf')

        categories = list(CategoryModel.objects.values_list('name', flat=True))
        use_mistral = (not self.debug_mode) or self.force_mistral

        if is_pdf:
            file_content = image_file.read()
            pdf_text = self._extract_text_from_pdf(file_content)
            if self._is_pdf_text_sufficient(pdf_text):
                logger.info(f"PDF com texto ({len(pdf_text)} chars), extração via texto direto")
                if use_mistral:
                    return self._extract_text_with_mistral(pdf_text, categories)
                else:
                    return self._extract_text_with_ollama(pdf_text, categories)

            if use_mistral and MISTRAL_SDK_AVAILABLE:
                try:
                    return self._extract_pdf_native_mistral(file_content, categories)
                except Exception as e:
                    logger.warning(f"Mistral PDF nativo falhou: {e}, usando conversão para imagem")

            file_base64, page_count = self._prepare_pdf_for_vision(file_content)
            if file_base64 is None:
                return {
                    'error': 'PDF vazio ou não foi possível converter.',
                    'description': '', 'amount': None, 'date': None,
                    'category_name': None, 'category_id': None,
                    'is_positive': True, 'confidence': 0,
                }
            logger.info(f"PDF convertido para imagem ({page_count} página(s))")

            if use_mistral:
                return self._extract_with_mistral(file_base64, 'image/png', categories)
            else:
                return self._extract_with_ollama(file_base64, 'image/png', categories)
        else:
            try:
                img = Image.open(image_file)
            except Exception as e:
                return {
                    'error': f'Erro ao ler imagem: {str(e)}',
                    'description': '', 'amount': None, 'date': None,
                    'category_name': None, 'category_id': None,
                    'is_positive': True, 'confidence': 0,
                }

            width, height = img.size
            if width < 50 or height < 50:
                return {
                    'error': f'Imagem muito pequena ({width}x{height}). Mínimo: 50x50 pixels.',
                    'description': '', 'amount': None, 'date': None,
                    'category_name': None, 'category_id': None,
                    'is_positive': True, 'confidence': 0,
                }

            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            file_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')

            if use_mistral:
                return self._extract_with_mistral(file_base64, 'image/png', categories)
            else:
                return self._extract_with_ollama(file_base64, 'image/png', categories)

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
                timeout=self.ocr_timeout
            )
            response.raise_for_status()

            result = response.json()
            ocr_text = result.get('response', '')

            # Tentar parsear JSON da resposta
            extracted = self._parse_fallback_json(ocr_text)
            if not extracted:
                # Se falhou, tentar parsing de texto livre
                extracted = self._parse_receipt_text(ocr_text, categories)

            extracted['raw_text'] = ocr_text

            normalized = self._normalize_extracted_data(extracted, categories)
            return normalized

        except Exception as e:
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

    def _extract_text_with_ollama(self, text: str, categories: list, multiple: bool = False) -> Dict[str, Any]:
        """Extrai dados de texto (PDF com texto selecionável) usando modelo de texto do Ollama."""
        ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
        ollama_text_model = getattr(settings, 'OLLAMA_TEXT_MODEL', None)
        ollama_model = ollama_text_model or getattr(settings, 'OLLAMA_OCR_MODEL', 'qwen3-vl:8b')

        categories_formatted = "\n".join([f"- {cat}" for cat in categories]) if categories else "- Outros"

        if multiple:
            prompt = f"""Analise este texto de lista/envelopes e retorne APENAS um array JSON.

CATEGORIAS DISPONÍVEIS (use EXATAMENTE estes nomes):
{categories_formatted}

Formatação NORMALIZAÇÃO:
- "Dízimo" → use "dízimo"
- "Oferta" ou "Ofertas" → use "oferta voluntária"

Formato OBRIGATÓRIO:
[
  {{"description": "Envelope 895 - dízimo", "amount": 2.50, "date": "2026-02-02", "category": "dízimo", "is_positive": true, "confidence": 90}},
]

Texto extraído do documento:
{text}

Retorne APENAS o array JSON, sem texto adicional."""
        else:
            prompt = f"""Extraia as informações deste comprovante de pagamento e retorne APENAS no formato JSON.

Categorias disponíveis:
{categories_formatted}

Retorne EXATAMENTE este JSON:
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
- is_positive: false (comprovantes são despesas), true (receitas/dízimos)
- confidence: 0-100 baseado na clareza dos dados

Texto extraído do comprovante:
{text}

Retorne APENAS o JSON, sem texto adicional."""

        try:
            payload = {
                'model': ollama_model,
                'prompt': prompt,
                'stream': False
            }

            response = requests.post(
                f'{ollama_host}/api/generate',
                json=payload,
                timeout=self.ocr_timeout
            )
            response.raise_for_status()

            result = response.json()
            ocr_text = result.get('response', '')

            logger.info(f"[OCR TEXTO OLLAMA] Resposta: {ocr_text[:200]}...")

            if multiple:
                transactions = self._parse_multiple_json(ocr_text, categories)
                return {'transactions': transactions}
            else:
                extracted = self._parse_fallback_json(ocr_text)
                if not extracted:
                    extracted = self._parse_receipt_text(ocr_text, categories)

                extracted['raw_text'] = ocr_text
                return self._normalize_extracted_data(extracted, categories)

        except Exception as e:
            if multiple:
                return {'error': f'Erro ao comunicar com Ollama: {str(e)}', 'transactions': []}
            return {
                'error': f'Erro ao comunicar com Ollama: {str(e)}',
                'description': '', 'amount': None, 'date': None,
                'category_name': None, 'category_id': None,
                'is_positive': True, 'confidence': 0,
            }

    def _extract_text_with_mistral(self, text: str, categories: list, multiple: bool = False) -> Dict[str, Any]:
        """Extrai dados de texto (PDF com texto) usando Mistral chat."""
        if not MISTRAL_SDK_AVAILABLE:
            if multiple:
                return {'error': 'SDK Mistral não instalado.', 'transactions': []}
            return {
                'error': 'SDK Mistral não instalado.',
                'description': '', 'amount': None, 'date': None,
                'category_name': None, 'category_id': None,
                'is_positive': True, 'confidence': 0,
            }

        if not hasattr(settings, 'MISTRAL_API_KEY') or not settings.MISTRAL_API_KEY:
            if multiple:
                return {'error': 'MISTRAL_API_KEY não configurado', 'transactions': []}
            return {
                'error': 'MISTRAL_API_KEY não configurado',
                'description': '', 'amount': None, 'date': None,
                'category_name': None, 'category_id': None,
                'is_positive': True, 'confidence': 0,
            }

        client = Mistral(api_key=settings.MISTRAL_API_KEY)
        categories_formatted = ", ".join(categories)

        if multiple:
            prompt = f"""Extraia TODAS as transações deste texto de lista/envelopes.

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

Texto extraído:
{text}

Retorne APENAS o array JSON."""
            system_msg = "Você é um assistente especializado em extrair dados de listas de transações. Responda APENAS com um array JSON válido, sem qualquer texto adicional."
        else:
            prompt = self._build_extraction_prompt(categories)
            prompt += f"\n\nTexto do comprovante:\n{text}"
            system_msg = "Você é um assistente especializado em extrair dados de comprovantes de pagamento. Responda APENAS com um JSON válido, sem qualquer texto adicional."

        try:
            model = getattr(settings, 'MISTRAL_MODEL', 'mistral-small-latest')

            chat_response = client.chat.complete(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000 if multiple else 1000,
                temperature=0.1
            )

            response_text = chat_response.choices[0].message.content
            logger.info(f"[OCR TEXTO MISTRAL] Resposta: {response_text[:200]}...")

            if multiple:
                result = json.loads(response_text)

                if isinstance(result, dict):
                    for key in ['transactions', 'data', 'results', 'items']:
                        if key in result and isinstance(result[key], list):
                            result = result[key]
                            break

                if not isinstance(result, list):
                    transactions = self._parse_multiple_json(response_text, categories)
                else:
                    transactions = [self._normalize_extracted_data(tx, categories) for tx in result]

                return {'transactions': transactions}
            else:
                extracted = json.loads(response_text)
                return self._normalize_extracted_data(extracted, categories)

        except Exception as e:
            if multiple:
                return {'error': f'Erro ao processar com Mistral: {str(e)}', 'transactions': []}
            return {
                'error': f'Erro ao processar com Mistral: {str(e)}',
                'description': '', 'amount': None, 'date': None,
                'category_name': None, 'category_id': None,
                'is_positive': True, 'confidence': 0,
            }

    def _extract_pdf_native_mistral(self, file_content: bytes, categories: list, multiple: bool = False) -> Dict[str, Any]:
        """Extrai dados de PDF usando Mistral OCR nativo (suporta múltiplas páginas)."""
        if not MISTRAL_SDK_AVAILABLE:
            raise Exception('SDK Mistral não instalado.')
        if not hasattr(settings, 'MISTRAL_API_KEY') or not settings.MISTRAL_API_KEY:
            raise Exception('MISTRAL_API_KEY não configurado')

        client = Mistral(api_key=settings.MISTRAL_API_KEY)
        pdf_base64 = base64.b64encode(file_content).decode('utf-8')

        ocr_response = client.ocr.process(
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}"
            },
            model="mistral-ocr-latest"
        )

        ocr_text = ""
        if hasattr(ocr_response, 'pages') and ocr_response.pages:
            for page in ocr_response.pages:
                if hasattr(page, 'markdown') and page.markdown:
                    ocr_text += page.markdown + "\n"

        if not ocr_text.strip():
            if multiple:
                return {'error': 'Nenhum texto encontrado no PDF.', 'transactions': []}
            return {
                'error': 'Nenhum texto encontrado no PDF.',
                'description': '', 'amount': None, 'date': None,
                'category_name': None, 'category_id': None,
                'is_positive': True, 'confidence': 0,
            }

        logger.info(f"[OCR PDF NATIVO MISTRAL] Extraído {len(ocr_text)} chars de {len(ocr_response.pages) if hasattr(ocr_response, 'pages') else '?'} páginas")

        return self._extract_text_with_mistral(ocr_text, categories, multiple=multiple)
        """
        Extrai múltiplas transações de uma imagem ou PDF (lista, envelopes, urna, etc).

        Args:
            image_file: Arquivo de imagem (JPEG, PNG, PDF)

        Returns:
            Dict com: transactions (array), error (opcional)
        """
        file_content = image_file.read()
        file_name = getattr(image_file, 'name', 'receipt.jpg')

        is_pdf = file_name.lower().endswith('.pdf')

        categories = list(CategoryModel.objects.values_list('name', flat=True))
        use_mistral = (not self.debug_mode) or self.force_mistral

        if is_pdf:
            pdf_text = self._extract_text_from_pdf(file_content)
            if self._is_pdf_text_sufficient(pdf_text):
                logger.info(f"PDF múltiplo com texto ({len(pdf_text)} chars), extração via texto direto")
                if use_mistral:
                    return self._extract_text_with_mistral(pdf_text, categories, multiple=True)
                else:
                    return self._extract_text_with_ollama(pdf_text, categories, multiple=True)

            if use_mistral and MISTRAL_SDK_AVAILABLE:
                try:
                    return self._extract_pdf_native_mistral(file_content, categories, multiple=True)
                except Exception as e:
                    logger.warning(f"Mistral PDF nativo falhou: {e}, usando conversão para imagem")

            file_base64, page_count = self._prepare_pdf_for_vision(file_content)
            if file_base64 is None:
                return {
                    'error': 'PDF vazio ou não foi possível converter.',
                    'transactions': []
                }
            logger.info(f"PDF múltiplo convertido para imagem ({page_count} página(s))")

            # Forçar Ollama para imagens também (Mistral instável)
            return self._extract_multiple_with_ollama(file_base64, 'image/png', categories)

        try:
            img = Image.open(io.BytesIO(file_content))
        except Exception as e:
            return {
                'error': f'Erro ao ler imagem: {str(e)}',
                'transactions': []
            }

        width, height = img.size
        if width < 50 or height < 50:
            return {
                'error': f'Imagem muito pequena ({width}x{height}).',
                'transactions': []
            }


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

        prompt = f"""Analise esta imagem de lista/envelopes e retorne APENAS um array JSON.

CATEGORIAS DISPONÍVEIS (use EXATAMENTE estes nomes, com a mesma grafia):
{categories_formatted}

EXEMPLOS DE NORMALIZAÇÃO:
- "Dízimo" no header → use "dízimo"
- "Missões" no header → use "missões"
- "Oferta" ou "Ofertas" → use "oferta voluntária"
- "Urnas" ou "Urna" → use "ofertas"

Formato OBRIGATÓRIO (retorne EXATAMENTE isto):
[
  {{"description": "Envelope 895 - dízimo", "amount": 2.50, "date": "2026-02-02", "category": "dízimo", "is_positive": true, "confidence": 90}},
  {{"description": "Envelope 895 - missões", "amount": 50.00, "date": "2026-02-02", "category": "missões", "is_positive": true, "confidence": 90}}
]

Regras IMPORTANTES:
- NÃO explique, NÃO use tabelas markdown
- Tabelas: cada coluna = uma transação. Use o NOME DO HEADER como categoria.
- NORMALIZE: use o nome EXATO da lista acima (ex: "dízimo" não "Dízimo")
- amount: número decimal positivo (ex: 2.50)
- date: YYYY-MM-DD ou hoje: {datetime.now().strftime('%Y-%m-%d')}
- is_positive: SEMPRE true. NUNCA false.
- confidence: 70 a 90

RETORNE APENAS O ARRAY JSON. COMECE COM [ E TERMINA COM ]."""

        try:
            payload = {
                'model': ollama_model,
                'prompt': prompt,
                'images': [file_base64],
                'stream': False
            }

            response = requests.post(
                f'{ollama_host}/api/generate',
                json=payload,
                timeout=self.ocr_timeout
            )
            response.raise_for_status()

            result = response.json()
            ocr_text = result.get('response', '')

            print(f'\n{"="*60}', flush=True)
            print(f'[OCR MULTIPLO OLLAMA] Resposta bruta:\n{ocr_text}', flush=True)
            print(f'{"="*60}', flush=True)

            transactions = self._parse_multiple_json(ocr_text, categories)

            print(f'[OCR MULTIPLO OLLAMA] Transacoes parseadas: {len(transactions)}', flush=True)
            for i, tx in enumerate(transactions):
                print(f'  TX {i}: raw_category={tx.get("raw_data", {}).get("category")} | category_name={tx.get("category_name")} | category_id={tx.get("category_id")}', flush=True)

            return {'transactions': transactions}

        except Exception as e:
            return {
                'error': f'Erro ao comunicar com Ollama: {str(e)}',
                'transactions': []
            }

    def _parse_single_fallback(self, text: str, categories: list) -> Dict[str, Any]:
        """Fallback parsing para resposta JSON malformada de single transaction."""
        # Tentar encontrar objeto JSON entre ```
        import re
        object_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if object_match:
            try:
                return json.loads(object_match.group(1))
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
                            break

        # Fallback final: retornar objeto vazio
        return {
            'description': 'Erro no parsing',
            'amount': None,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'category': 'Outros',
            'is_positive': True,
            'confidence': 10
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

Retorne APENAS um objeto JSON neste formato:
{{
  "transactions": [
    {{"description": "Envelope X - Categoria", "amount": 100.00, "date": "2026-02-02", "category": "Dízimos", "is_positive": true, "confidence": 90}}
  ]
}}

Regras:
- Cada envelope com múltiplas categorias = múltiplas transações
- is_positive: SEMPRE true para envelopes/dízimos/ofertas. Use false APENAS para despesas.
- amount: número decimal
- date: YYYY-MM-DD ou data de hoje
- Retorne APENAS o objeto JSON"""

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
                        "content": "Você é um assistente especializado em extrair dados de listas de transações. Responda APENAS com JSON válido, sem markdown, sem explicações, sem texto adicional. O JSON deve ser parseável diretamente."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nTexto extraído:\n{ocr_text}"
                    }
                ],
                max_tokens=8000,
                temperature=0.1
            )

            response_text = chat_response.choices[0].message.content

            print(f'\n{"="*60}', flush=True)
            print(f'[OCR MULTIPLO MISTRAL] Resposta bruta (len={len(response_text)}):\n{response_text}', flush=True)
            print(f'{"="*60}', flush=True)

            # Tentar parsear JSON diretamente
            try:
                result = json.loads(response_text)
                print(f'[OCR MULTIPLO MISTRAL] JSON parseado com sucesso: tipo={type(result)}', flush=True)
            except json.JSONDecodeError as e:
                print(f'[OCR MULTIPLO MISTRAL] JSON direto falhou: {e}, tentando Ollama diretamente', flush=True)
                try:
                    return self._extract_multiple_with_ollama(file_base64, file_type, categories)
                except Exception as ollama_e:
                    print(f'[OCR MULTIPLO MISTRAL] Ollama também falhou: {ollama_e}, tentando parsing manual', flush=True)
                    try:
                        transactions = self._parse_multiple_json(response_text, categories)
                        print(f'[OCR MULTIPLO MISTRAL] Parsing manual conseguiu {len(transactions)} transacoes', flush=True)
                        return {'transactions': transactions}
                    except Exception as parse_e:
                        print(f'[OCR MULTIPLO MISTRAL] Parsing manual também falhou: {parse_e}', flush=True)
                        raise e  # Re-raise the original JSON error

            print(f'[OCR MULTIPLO MISTRAL] JSON tipo={type(result).__name__} keys={list(result.keys()) if isinstance(result, dict) else "N/A"}', flush=True)

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

            print(f'[OCR MULTIPLO MISTRAL] Transacoes normalizadas: {len(transactions)}', flush=True)
            for i, tx in enumerate(transactions):
                print(f'  TX {i}: raw_category={tx.get("raw_data", {}).get("category")} | category_name={tx.get("category_name")} | category_id={tx.get("category_id")}', flush=True)

            return {'transactions': transactions}

        except Exception as e:
            error_str = str(e).lower()
            if 'api error' in error_str or 'status 500' in error_str or 'service unavailable' in error_str:
                print(f'[OCR MULTIPLO] Mistral API indisponível ({e}), tentando Ollama', flush=True)
                try:
                    return self._extract_multiple_with_ollama(file_base64, file_type, categories)
                except Exception as ollama_e:
                    print(f'[OCR MULTIPLO] Ollama fallback também falhou: {ollama_e}', flush=True)

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
                max_tokens=2000,
                temperature=0.1
            )

            response_text = chat_response.choices[0].message.content

            print(f'\n{"="*50}', flush=True)
            print(f'[OCR SINGLE MISTRAL] Resposta bruta (len={len(response_text) if response_text else 0}):\n{response_text}', flush=True)
            print(f'{"="*50}', flush=True)

            if not response_text:
                print(f'[OCR SINGLE MISTRAL] Resposta vazia!', flush=True)
                raise Exception("Resposta vazia da Mistral")

            try:
                extracted = json.loads(response_text)
                print(f'[OCR SINGLE MISTRAL] JSON parseado com sucesso: tipo={type(extracted)}', flush=True)
            except json.JSONDecodeError as e:
                print(f'[OCR SINGLE MISTRAL] JSON parsing falhou: {e}, tentando fallback', flush=True)
                # Fallback: tentar extrair dados do texto
                extracted = self._parse_single_fallback(response_text, categories)
                print(f'[OCR SINGLE MISTRAL] Fallback result: {extracted}', flush=True)

            print(f'[OCR SINGLE MISTRAL] Chamando normalize com: {type(extracted)} - {extracted}', flush=True)
            return self._normalize_extracted_data(extracted, categories)

        except Exception as e:
            error_str = str(e).lower()
            if 'api error' in error_str or 'status 500' in error_str or 'service unavailable' in error_str:
                print(f'[OCR SINGLE] Mistral API indisponível ({e}), tentando Ollama', flush=True)
                try:
                    return self._extract_with_ollama(file_base64, file_type, categories)
                except Exception as ollama_e:
                    print(f'[OCR SINGLE] Ollama fallback também falhou: {ollama_e}', flush=True)

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

        # Tentar extrair do formato estruturado (TOTAL: | DATE: | DESC: |)
        total_match = re.search(r'TOTAL:\s*([^\n]+?)(?=DATE:|DESC:|$)', text, re.IGNORECASE)
        date_match = re.search(r'DATE:\s*([^\n]+?)(?=TOTAL:|DESC:|$)', text, re.IGNORECASE)
        desc_match = re.search(r'DESC:\s*([^\n]+?)(?=TOTAL:|DATE:|$)', text, re.IGNORECASE)

        if date_match or desc_match or total_match:
            # Formato estruturado encontrado
            if date_match:
                date_str = date_match.group(1).strip()
                result['date'] = self._parse_date(date_str)
            if desc_match:
                result['description'] = desc_match.group(1).strip()
            if total_match:
                amount_str = total_match.group(1).strip()
                result['amount'] = self._parse_amount(amount_str)

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
                        break
                except ValueError:
                    pass

        # Se não achou TOTAL, tentar somar todos os valores positivos encontrados
        if not result['amount']:
            # Encontrar todos os valores monetários
            all_values = re.findall(r'-?\s*R?\$?\s*([\d.]+,\d{2})', text)
            total_sum = 0
            for val_str in all_values:
                try:
                    val = float(val_str.replace('.', '').replace(',', '.'))
                    # Somar apenas valores positivos razoáveis (ignorar descontos negativos)
                    if 0.50 < val < 10000:  # Valores razoáveis de item
                        total_sum += val
                except ValueError:
                    pass
            if total_sum > 1:
                result['amount'] = total_sum

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
                        return category

        # Se não achou, tentar categoria mais próxima
        for category in categories:
            if category.lower() in combined:
                return category

        return 'Outros'

    def _normalize_extracted_data(self, data: Dict, categories: list) -> Dict[str, Any]:
        """Normaliza e valida os dados extraídos."""
        if data is None:
            data = {}

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

        # Função helper para match case-insensitive
        def find_category_match(name_to_find):
            if not name_to_find:
                return None
            # Primeiro tenta match exato case-insensitive
            name_lower = name_to_find.lower()
            for cat in categories:
                if cat.lower() == name_lower:
                    return cat
            # Depois tenta partial match (para casos como Dízimos -> dízimo)
            for cat in categories:
                cat_lower = cat.lower()
                if name_lower in cat_lower or cat_lower in name_lower:
                    return cat
            return None

        # Se a categoria do JSON existe no BD (case-insensitive), usar ela
        matched_category = find_category_match(category_name)
        if matched_category:
            category_name = matched_category
        else:
            # Categoria não existe - tentar inferir
            raw_text = data.get('raw_text', '')
            inferred = self._infer_category(description, raw_text, categories)
            if inferred:
                category_name = inferred
                print(f'[CATEGORY] Inferida: {category_name} de desc="{description}" raw="{raw_text[:100]}"', flush=True)
            else:
                print(f'[CATEGORY] Não conseguiu inferir de desc="{description}" raw="{raw_text[:100]}", usando Outros', flush=True)

        # Buscar ID da categoria
        category_id = None
        try:
            category = CategoryModel.objects.filter(name=category_name).first()
            if category:
                category_id = category.id
        except Exception:
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

    def extract_multiple_from_receipt(self, image_file) -> Dict[str, Any]:
        """
        Extrai múltiplas transações de uma imagem ou PDF (lista, envelopes, urna, etc).

        Args:
            image_file: Arquivo de imagem (JPEG, PNG, PDF)

        Returns:
            Dict com: transactions (array), error (opcional)
        """
        file_name = getattr(image_file, 'name', 'receipt.jpg')
        content_type = getattr(image_file, 'content_type', '').lower()

        is_pdf = (file_name.lower().endswith('.pdf') or
                    content_type == 'application/pdf')

        categories = list(CategoryModel.objects.values_list('name', flat=True))
        use_mistral = (not self.debug_mode) or self.force_mistral

        print(f'[OCR MULTIPLO] file_name={file_name} content_type={content_type} is_pdf={is_pdf} use_mistral={use_mistral} debug_mode={self.debug_mode} force_mistral={self.force_mistral}', flush=True)

        if is_pdf:
            file_content = image_file.read()
            pdf_text = self._extract_text_from_pdf(file_content)
            if self._is_pdf_text_sufficient(pdf_text):
                logger.info(f"PDF múltiplo com texto ({len(pdf_text)} chars), extração via texto direto")
                if use_mistral:
                    return self._extract_text_with_mistral(pdf_text, categories, multiple=True)
                else:
                    return self._extract_text_with_ollama(pdf_text, categories, multiple=True)

            if use_mistral and MISTRAL_SDK_AVAILABLE:
                try:
                    return self._extract_pdf_native_mistral(file_content, categories, multiple=True)
                except Exception as e:
                    logger.warning(f"Mistral PDF nativo falhou: {e}, usando conversão para imagem")

            file_base64, page_count = self._prepare_pdf_for_vision(file_content)
            if file_base64 is None:
                return {
                    'error': 'PDF vazio ou não foi possível converter.',
                    'transactions': []
                }
            logger.info(f"PDF múltiplo convertido para imagem ({page_count} página(s))")

            # Forçar Ollama para PDFs por enquanto (Mistral com problemas)
            return self._extract_multiple_with_ollama(file_base64, 'image/png', categories)
        else:
            # Handle images (non-PDF)
            try:
                img = Image.open(image_file)
            except Exception as e:
                return {
                    "error": f"Erro ao ler imagem: {str(e)}",
                    "transactions": []
                }

            width, height = img.size
            if width < 50 or height < 50:
                return {
                    "error": f"Imagem muito pequena ({width}x{height}). Mínimo: 50x50 pixels.",
                    "transactions": []
                }

            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            file_base64 = base64.b64encode(img_buffer.read()).decode("utf-8")

            if use_mistral:
                return self._extract_multiple_with_mistral(file_base64, "image/png", categories)
            else:
                return self._extract_multiple_with_ollama(file_base64, "image/png", categories)
