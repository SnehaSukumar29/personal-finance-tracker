import unittest

from finance_tracker.db import Database
from finance_tracker.reports import build_monthly_report


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_add_list_delete(self):
        tx_id = self.db.add_transaction("expense", 1250, "groceries", "2026-10-05", "shop")
        rows = self.db.list_transactions()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].amount_pence, 1250)
        self.assertTrue(self.db.delete_transaction(tx_id))
        self.assertFalse(self.db.delete_transaction(tx_id))
        self.assertEqual(self.db.list_transactions(), [])

    def test_filters(self):
        self.db.add_transaction("expense", 100, "food", "2026-09-30")
        self.db.add_transaction("expense", 200, "food", "2026-10-01")
        self.db.add_transaction("income", 300, "salary", "2026-10-01")
        self.assertEqual(len(self.db.list_transactions(month="2026-10")), 2)
        self.assertEqual(len(self.db.list_transactions(tx_type="income")), 1)
        self.assertEqual(len(self.db.list_transactions(category="food")), 2)

    def test_sql_injection_payload_is_treated_as_data(self):
        payload = "food' OR '1'='1"
        self.db.add_transaction("expense", 100, "food", "2026-10-01")
        self.assertEqual(self.db.list_transactions(category=payload), [])

    def test_database_constraints_reject_bad_rows(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_transaction("expense", -100, "food", "2026-10-01")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_transaction("gift", 100, "food", "2026-10-01")

    def test_budget_upsert(self):
        self.db.set_budget("food", 1000)
        self.db.set_budget("food", 2000)
        self.assertEqual(self.db.get_budgets(), {"food": 2000})
        self.assertTrue(self.db.remove_budget("food"))
        self.assertEqual(self.db.get_budgets(), {})


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.db.add_transaction("income", 200000, "salary", "2026-10-01")
        self.db.add_transaction("expense", 18000, "groceries", "2026-10-03")
        self.db.add_transaction("expense", 3000, "transport", "2026-10-04")
        self.db.add_transaction("expense", 9999, "groceries", "2026-09-30")  # other month
        self.db.set_budget("groceries", 20000)
        self.db.set_budget("transport", 2500)
        self.db.set_budget("eating out", 5000)

    def tearDown(self):
        self.db.close()

    def test_totals(self):
        r = build_monthly_report(self.db, "2026-10")
        self.assertEqual(r.income_pence, 200000)
        self.assertEqual(r.expense_pence, 21000)
        self.assertEqual(r.net_pence, 179000)
        self.assertEqual(r.savings_rate, 89.5)

    def test_budget_statuses(self):
        lines = {l.category: l for l in build_monthly_report(self.db, "2026-10").lines}
        self.assertEqual(lines["groceries"].status, "WARNING")  # 90%
        self.assertEqual(lines["transport"].status, "OVER")     # 120%
        self.assertEqual(lines["eating out"].status, "OK")      # 0%
        self.assertEqual(lines["groceries"].percent_used, 90.0)

    def test_empty_month(self):
        r = build_monthly_report(self.db, "2025-01")
        self.assertEqual(r.net_pence, 0)
        self.assertIsNone(r.savings_rate)


if __name__ == "__main__":
    unittest.main()
