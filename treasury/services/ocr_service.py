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
        if self.debug_mode:
            # Desenvolvimento: Ollama
            result = self._extract_with_ollama(file_base64, 'image/png', categories)
        else:
            # Produção: Mistral
            result = self._extract_with_mistral(file_base64, 'image/png', categories)

        return result

    def _extract_with_ollama(self, file_base64: str, file_type: str, categories: list) -> Dict[str, Any]:
        """
        Extrai dados usando Ollama com Ministral-3 (modelo multimodal).

        Args:
            file_base64: Arquivo em base64
            file_type: Tipo MIME do arquivo
            categories: Lista de categorias disponíveis

        Returns:
            Dict com os dados extraídos
        """
        ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
        ollama_model = getattr(settings, 'OLLAMA_OCR_MODEL', 'deepseek-ocr:3b')

        # Prompt simples para extrair texto (não pede JSON)
        # Usar prompt curto que funciona no curl
        prompt = "Extract text from image."

        try:
            print(f"[OCR] Enviando para Ollama (modelo: {ollama_model})...")
            print(f"[OCR] Prompt: {prompt[:100]}...")

            payload = {
                'model': ollama_model,
                'prompt': prompt,
                'images': [file_base64],
                'stream': False,
                'options': {
                    'temperature': 0.0,
                    'num_predict': 4000,  # Aumentado para capturar textos maiores
                }
            }

            print(f"[OCR] Payload (primeiros 200 chars do JSON): {str(payload)[:200]}...")

            response = requests.post(
                f'{ollama_host}/api/generate',
                json=payload,
                timeout=120
            )
            print(f"[OCR] Status code: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            ocr_text = result.get('response', '')

            print(f"[OCR] Texto extraído pelo OCR:")
            print(f"[OCR] {ocr_text[:800]}...")

            # Parsear o texto extraído para encontrar os dados
            extracted = self._parse_receipt_text(ocr_text, categories)
            # Salvar texto cru para inferência de categoria
            extracted['raw_text'] = ocr_text
            print(f"[OCR] Dados parseados:")
            print(f"[OCR]   description: {extracted.get('description')}")
            print(f"[OCR]   amount: {extracted.get('amount')}")
            print(f"[OCR]   date: {extracted.get('date')}")
            print(f"[OCR]   category: {extracted.get('category')}")
            print(f"[OCR]   is_positive: {extracted.get('is_positive')}")

            normalized = self._normalize_extracted_data(extracted, categories)
            print(f"[OCR] Dados normalizados:")
            print(f"[OCR]   description: {normalized.get('description')}")
            print(f"[OCR]   amount: {normalized.get('amount')}")
            print(f"[OCR]   date: {normalized.get('date')}")
            print(f"[OCR]   category: {normalized.get('category_name')}")
            print(f"[OCR]   is_positive: {normalized.get('is_positive')}")
            print(f"[OCR]   confidence: {normalized.get('confidence')}")

            return normalized

        except requests.RequestException as e:
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
        categories_list = '", "'.join(categories) if categories else 'Outros'

        return f"""Analise este comprovante de pagamento e extraia as seguintes informações:

1. **description**: Descrição breve do que foi pago (ex: "Compra no Mercado", "Pagamento de Luz")
2. **amount**: Valor numérico (apenas números, sem pontos ou vírgulas)
3. **date**: Data do pagamento no formato AAAA-MM-DD
4. **category**: Escolha a MELHOR categoria desta lista: "{categories_list}"
5. **is_positive**: true se for RECEITA (entrada), false se for DESPESA (saída)
6. **confidence**: Nível de confiança de 0 a 100

Regras:
- Se for um comprovante de pagamento/fatura, is_positive deve ser false
- Se for um comprovante de recebimento/depósito, is_positive deve ser true
- Se não conseguir identificar a categoria, use "Outros"
- A data deve estar no formato AAAA-MM-DD. Se não conseguir identificar, use a data atual

Responda APENAS com um JSON válido neste formato exato:
{{
    "description": "descrição",
    "amount": 0.00,
    "date": "2024-01-15",
    "category": "nome da categoria",
    "is_positive": false,
    "confidence": 85
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

        print(f"[OCR] Parseando texto: {text[:300]}...")

        # Extrair valor - procurar TOTAL primeiro, depois outros valores
        amount_patterns = [
            # Padrões com TOTAL/TOTAL A PAGAR/VALOR A PAGAR
            r'(?:TOTAL|VALOR.*?PAGAR|SOMA)\s*(?:R\$\s*)?[\d]{1,6}[,\.]\d{2}',
            r'(?:TOTAL|VALOR.*?PAGAR)\s*:\s*R?\$?\s*[\d]{1,6}[,\.]\d{2}',
            # Depois genéricos (limitado a valores razoáveis)
            r'R\$\s*[\d]{1,6}[,\.]\d{2}',
            r'[\d]{1,6}[,\.]\d{2}(?=\s*$)',
        ]

        for pattern in amount_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            # Pegar o último match (geralmente o total é o último valor)
            if matches:
                amount_str = matches[-1].group(0)
                # Limpar e converter
                amount_str = re.sub(r'[^\d.,]', '', amount_str)
                amount_str = amount_str.replace('.', '').replace(',', '.')
                try:
                    val = float(amount_str)
                    # Ignorar valores absurdos (> 100000 provavelmente é erro/CNPJ)
                    if val < 100000:
                        result['amount'] = val
                        print(f"[OCR] Valor encontrado: {result['amount']} (padrão: {pattern})")
                        break
                except ValueError:
                    pass

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

        # Extrair descrição - pegar nome do estabelecimento (primeira linha não numérica)
        # Dividir por palavras-chave comuns
        text_parts = re.split(r'CNPJ|Documento Auxiliar|ITEM C00160|---', text)
        first_part = text_parts[0].strip() if text_parts else text

        # Pegar até 4 primeiras palavras (geralmente o nome da empresa)
        words = first_part.split()
        if words:
            # Pegar até 4 palavras, mas não muito curto
            for i in range(3, min(len(words) + 1, 7)):
                desc = ' '.join(words[:i])
                if len(desc) >= 8 and len(desc) < 60:  # Entre 8 e 60 caracteres
                    result['description'] = desc
                    print(f"[OCR] Descrição encontrada: {result['description']}")
                    break

        # Se não achou descrição adequada, usar padrão
        if not result['description']:
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
                          'quero-quero', 'c%C', 'sodimaco', 'mm', 'telhanorte'],
            # Transporte
            'Transporte': ['uber', '99 taxi', 'taxi', 'posto', 'gasolina', 'combustível', 'estacionamento',
                          'pedágio', 'transporte', 'ônibus', 'metrô'],
            # Alimentação
            'Alimentação': ['restaurante', 'lanchonete', 'fast food', 'mc donalds', 'burger king',
                           'pizza', ' Delivery', 'ifood', 'rappi'],
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

        # Categoria - usar inferência se for "Outros" ou não existir
        category_name = data.get('category', 'Outros')
        if category_name not in categories or category_name == 'Outros':
            # Tentar inferir categoria da descrição e texto cru
            raw_text = data.get('raw_text', '')
            category_name = self._infer_category(description, raw_text, categories)

        # Buscar ID da categoria
        category_id = None
        try:
            category = CategoryModel.objects.filter(name=category_name).first()
            if category:
                category_id = category.id
            elif categories:
                # Se não achou, usar a primeira disponível
                category = CategoryModel.objects.filter(name__in=categories).first()
                category_id = category.id if category else None
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
