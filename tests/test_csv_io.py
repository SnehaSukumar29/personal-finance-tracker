import csv
import os
import tempfile
import unittest

from finance_tracker.csv_io import (
    CsvImportError,
    export_csv,
    import_csv,
    sanitise_cell,
)
from finance_tracker.db import Database


class CsvTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def write(self, name, text):
        with open(self.path(name), "w", newline="", encoding="utf-8") as fh:
            fh.write(text)
        return self.path(name)

    def test_formula_injection_is_neutralised(self):
        for payload in ["=1+1", "+1", "-1", "@SUM(A1)", "\tx"]:
            with self.subTest(payload=payload):
                self.assertTrue(sanitise_cell(payload).startswith("'"))
        self.assertEqual(sanitise_cell("normal"), "normal")

    def test_export_writes_sanitised_note_and_two_decimal_amounts(self):
        self.db.add_transaction("expense", 1250, "food", "2026-10-01", "=HYPERLINK(\"evil\")")
        export_csv(self.db, self.path("out.csv"))
        with open(self.path("out.csv"), newline="", encoding="utf-8") as fh:
            row = list(csv.DictReader(fh))[0]
        self.assertEqual(row["amount"], "12.50")
        self.assertTrue(row["note"].startswith("'="))

    def test_round_trip(self):
        self.db.add_transaction("income", 210000, "salary", "2026-10-01", "pay")
        self.db.add_transaction("expense", 1250, "food", "2026-10-02", "-discount")
        export_csv(self.db, self.path("out.csv"))
        fresh = Database(":memory:")
        self.assertEqual(import_csv(fresh, self.path("out.csv")), 2)
        original = [(t.type, t.amount_pence, t.category, t.tx_date, t.note) for t in self.db.list_transactions()]
        imported = [(t.type, t.amount_pence, t.category, t.tx_date, t.note) for t in fresh.list_transactions()]
        self.assertEqual(original, imported)
        fresh.close()

    def test_import_is_all_or_nothing(self):
        path = self.write("bad.csv",
            "date,type,amount,category,note\n"
            "2026-10-01,expense,10.00,food,ok\n"
            "2026-10-02,expense,abc,food,bad amount\n"
            "2026-02-30,expense,5,food,bad date\n")
        with self.assertRaises(CsvImportError) as ctx:
            import_csv(self.db, path)
        self.assertEqual(len(ctx.exception.errors), 2)
        self.assertIn("Line 3", ctx.exception.errors[0])
        self.assertEqual(self.db.list_transactions(), [])  # nothing saved

    def test_import_missing_columns(self):
        path = self.write("cols.csv", "date,amount\n2026-10-01,5\n")
        with self.assertRaises(CsvImportError):
            import_csv(self.db, path)


if __name__ == "__main__":
    unittest.main()
