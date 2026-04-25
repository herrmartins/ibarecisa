import json
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from worship.utils.service_parser import (
    _empty_payload,
    _normalize_payload,
    _parse_json_content,
    generate_service_with_llm,
)


class EmptyPayloadTestCase(TestCase):
    def test_structure(self):
        payload = _empty_payload()
        self.assertEqual(payload["title"], "Culto")
        self.assertIsNone(payload["service_date"])
        self.assertEqual(payload["service_kind"], "REGULAR")
        self.assertEqual(payload["songs"], [])
        self.assertEqual(payload["confidence"], 0.0)


class ParseJsonContentTestCase(TestCase):
    def test_valid_json(self):
        data = {"title": "Culto", "service_date": "2026-05-01"}
        result = _parse_json_content(json.dumps(data))
        self.assertEqual(result["title"], "Culto")

    def test_json_inside_markdown(self):
        content = '```json\n{"title": "Culto"}\n```'
        result = _parse_json_content(content)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Culto")

    def test_json_embedded_in_text(self):
        content = 'Aqui está o resultado: {"title": "Culto", "service_kind": "REGULAR"} fim'
        result = _parse_json_content(content)
        self.assertIsNotNone(result)

    def test_invalid_json(self):
        result = _parse_json_content("não é JSON")
        self.assertIsNone(result)

    def test_empty_string(self):
        result = _parse_json_content("")
        self.assertIsNone(result)

    def test_none(self):
        result = _parse_json_content(None)
        self.assertIsNone(result)


class NormalizePayloadTestCase(TestCase):
    def test_valid_kind_preserved(self):
        payload = _normalize_payload({"service_kind": "COMMUNION"})
        self.assertEqual(payload["service_kind"], "COMMUNION")

    def test_invalid_kind_defaults_regular(self):
        payload = _normalize_payload({"service_kind": "INVALID"})
        self.assertEqual(payload["service_kind"], "REGULAR")

    def test_songs_filtered(self):
        payload = _normalize_payload({
            "songs": [
                {"order_ref": 1, "song_snapshot": "CC 291"},
                {"order_ref": 2, "song_snapshot": ""},
                {"order_ref": None, "song_snapshot": "  "},
            ]
        })
        self.assertEqual(len(payload["songs"]), 1)
        self.assertEqual(payload["songs"][0]["song_snapshot"], "CC 291")

    def test_empty_title_defaults(self):
        payload = _normalize_payload({"title": ""})
        self.assertEqual(payload["title"], "Culto")

    def test_missing_date_is_none(self):
        payload = _normalize_payload({})
        self.assertIsNone(payload["service_date"])

    def test_empty_program_html_gets_default(self):
        payload = _normalize_payload({"program_html": ""})
        self.assertIn("não detectada", payload["program_html"])

    def test_order_ref_none_when_missing(self):
        payload = _normalize_payload({
            "songs": [{"song_snapshot": "Hino 1"}]
        })
        self.assertIsNone(payload["songs"][0]["order_ref"])


@override_settings(MISTRAL_API_KEY="test-key", MISTRAL_MODEL="test-model")
class GenerateServiceWithLlmTestCase(TestCase):
    @patch("worship.utils.service_parser.requests.post")
    def test_successful_generation(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({
                "title": "Culto de Ceia",
                "service_date": "2026-05-01",
                "service_kind": "COMMUNION",
                "leaders_text": "Dirigente: Pr. João",
                "program_html": "<ol><li>Hino</li></ol>",
                "songs": [{"order_ref": 1, "song_snapshot": "CC 291"}],
            })}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = generate_service_with_llm("Texto do culto de ceia...")
        self.assertEqual(result["title"], "Culto de Ceia")
        self.assertEqual(result["source"], "llm")
        self.assertEqual(len(result["songs"]), 1)

    @patch("worship.utils.service_parser.requests.post")
    def test_api_error_returns_empty(self, mock_post):
        mock_post.side_effect = Exception("API error")
        result = generate_service_with_llm("Texto qualquer")
        self.assertEqual(result["source"], "empty")
        self.assertEqual(result["confidence"], 0.0)

    def test_empty_raw_text(self):
        result = generate_service_with_llm("")
        self.assertEqual(result["source"], "empty")

    def test_none_raw_text(self):
        result = generate_service_with_llm(None)
        self.assertEqual(result["source"], "empty")

    @override_settings(MISTRAL_API_KEY="")
    def test_no_api_key(self):
        result = generate_service_with_llm("Texto do culto")
        self.assertEqual(result["source"], "empty")

    @patch("worship.utils.service_parser.requests.post")
    def test_model_hint_passed(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "{}"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        generate_service_with_llm("Texto", model_hint="manter formato tradicional")
        call_args = mock_post.call_args
        messages = call_args[1]["json"]["messages"][0]["content"]
        self.assertIn("manter formato tradicional", messages)
