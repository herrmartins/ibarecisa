import unittest
from datetime import datetime
from secretarial.utils.date_utils import date_to_words


class TestDateToWords(unittest.TestCase):
    def test_valid_date_conversion(self):
        # Test converting a valid date to words
        result = date_to_words("2023-12-25")
        self.assertEqual(result, "25 de dezembro de 2023, ")

    def test_invalid_date_format(self):
        # Test handling of invalid date format
        result = date_to_words("2023/12/25")
        self.assertEqual(result, "Invalid date format. Please use YYYY-MM-DD.")

    def test_leap_year(self):
        # Test a leap year date
        result = date_to_words("2024-02-29")
        self.assertEqual(result, "29 de fevereiro de 2024, ")

    def test_edge_cases(self):
        # Test edge cases such as the earliest and latest allowable dates
        result_earliest = date_to_words("0001-01-01")
        result_latest = date_to_words("9999-12-31")
        self.assertEqual(result_earliest, "1 de janeiro de 0001, ")
        self.assertEqual(result_latest, "31 de dezembro de 9999, ")


if __name__ == "__main__":
    unittest.main()
