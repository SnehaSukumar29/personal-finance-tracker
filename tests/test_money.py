import unittest

from finance_tracker.money import format_pence, parse_amount


class ParseAmountTests(unittest.TestCase):
    def test_valid_amounts(self):
        cases = {"12": 1200, "12.5": 1250, "12.50": 1250, "0.01": 1, "£1,200.99": 120099}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(parse_amount(text), expected)

    def test_no_float_rounding_errors(self):
        # 0.1 + 0.2 != 0.3 in floats - integer pence avoids this entirely.
        self.assertEqual(parse_amount("0.10") + parse_amount("0.20"), parse_amount("0.30"))

    def test_rejects_invalid(self):
        for bad in ["", "abc", "0", "-5", "12.345", "NaN", "Infinity", "1e3x", "999999999999"]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_amount(bad)


class FormatPenceTests(unittest.TestCase):
    def test_format(self):
        self.assertEqual(format_pence(0), "£0.00")
        self.assertEqual(format_pence(5), "£0.05")
        self.assertEqual(format_pence(123456), "£1,234.56")
        self.assertEqual(format_pence(-1234), "-£12.34")


if __name__ == "__main__":
    unittest.main()
