import unittest
from datetime import datetime
from secretarial.utils.date_utils import date_to_words


class TestDateToWords(unittest.TestCase):
    def test_valid_date_conversion(self):
        # Test a valid date conversion
        input_date = "2023-12-30"
        expected_output = "30 de dezembro de 2023, "
        self.assertEqual(date_to_words(input_date), expected_output)

    def test_invalid_date_format(self):
        # Test invalid date format
        input_date = "2023/12/30"  # Incorrect format
        expected_output = "Invalid date format. Please use YYYY-MM-DD."
        self.assertEqual(date_to_words(input_date), expected_output)

    def test_invalid_date(self):
        # Test an invalid date (e.g., February 30)
        input_date = "2023-02-30"  # February 30 doesn't exist
        expected_output = "Invalid date format. Please use YYYY-MM-DD."
        self.assertEqual(date_to_words(input_date), expected_output)

    # Add more test cases as needed


if __name__ == "__main__":
    unittest.main()
