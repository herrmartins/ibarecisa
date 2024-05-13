from django.test import TestCase
from secretarial.utils.topdfutils import render_to_pdf
from django.template.exceptions import TemplateDoesNotExist
import unittest


class RenderToPDFTestCase(TestCase):
    def test_render_to_pdf_valid(self):
        context = {
            "name": "My Church",
            "CNPJ": "12312231223",
            "address": "123 Main St, City, Country",
            "contact_email": "info@mychurch.com",
            "phone": "",
        }

        pdf = render_to_pdf("secretarial/minute_pdf.html", context)

        self.assertIsNotNone(pdf)
        self.assertIsInstance(pdf, bytes)

    def test_render_to_pdf_invalid_template(self):
        invalid_path = "invalid/template/path.html"
        try:
            response = render_to_pdf(invalid_path)
            self.assertIsNone(response)
        except TemplateDoesNotExist:
            pass

    def test_render_to_pdf_empty_context(self):
        empty_context = {}
        pdf = render_to_pdf("secretarial/minute_pdf.html", empty_context)
        self.assertIsNotNone(pdf)
        self.assertIsInstance(pdf, bytes)


if __name__ == "__main__":
    unittest.main()
