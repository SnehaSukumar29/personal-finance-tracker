import unittest

from finance_tracker.validation import (
    validate_category,
    validate_date,
    validate_month,
    validate_note,
    validate_type,
)


class ValidationTests(unittest.TestCase):
    def test_type(self):
        self.assertEqual(validate_type(" Income "), "income")
        with self.assertRaises(ValueError):
            validate_type("transfer")

    def test_category_normalised_to_lowercase(self):
        self.assertEqual(validate_category("Eating Out"), "eating out")

    def test_category_rejects_injection_style_input(self):
        for bad in ["", "'; DROP TABLE transactions;--", "=cmd", "a" * 41, "<script>"]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_category(bad)

    def test_date(self):
        self.assertEqual(validate_date("2026-02-28"), "2026-02-28")
        for bad in ["2026-02-30", "28/02/2026", "tomorrow"]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_date(bad)

    def test_month(self):
        self.assertEqual(validate_month("2026-10"), "2026-10")
        for bad in ["2026-13", "2026-1", "Oct 2026"]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_month(bad)

    def test_note_strips_control_characters_and_limits_length(self):
        self.assertEqual(validate_note("hi\x1b[31mthere"), "hi[31mthere")
        with self.assertRaises(ValueError):
            validate_note("x" * 201)


if __name__ == "__main__":
    unittest.main()
