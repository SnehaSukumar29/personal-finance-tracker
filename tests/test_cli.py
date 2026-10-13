import contextlib
import io
import os
import tempfile
import unittest

from finance_tracker.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "test.db")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--db", self.db, *args])
        return code, out.getvalue(), err.getvalue()

    def test_add_and_report(self):
        self.assertEqual(self.run_cli("add", "income", "1000", "salary", "--date", "2026-10-01")[0], 0)
        self.assertEqual(self.run_cli("add", "expense", "250.50", "rent", "--date", "2026-10-02")[0], 0)
        code, out, _ = self.run_cli("report", "--month", "2026-10")
        self.assertEqual(code, 0)
        self.assertIn("£749.50", out)

    def test_invalid_input_returns_error_code(self):
        code, _, err = self.run_cli("add", "expense", "12.999", "food")
        self.assertEqual(code, 1)
        self.assertIn("two decimal places", err)

    def test_delete_missing_id(self):
        code, _, err = self.run_cli("delete", "999")
        self.assertEqual(code, 1)
        self.assertIn("No transaction", err)


if __name__ == "__main__":
    unittest.main()
