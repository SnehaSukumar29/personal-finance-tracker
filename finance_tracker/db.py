"""SQLite storage layer.

Every query uses parameter binding (?) - user input is never concatenated
into SQL, which prevents SQL injection.
"""
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    type         TEXT    NOT NULL CHECK (type IN ('income', 'expense')),
    amount_pence INTEGER NOT NULL CHECK (amount_pence > 0),
    category     TEXT    NOT NULL,
    tx_date      TEXT    NOT NULL,
    note         TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions (tx_date);

CREATE TABLE IF NOT EXISTS budgets (
    category     TEXT PRIMARY KEY,
    amount_pence INTEGER NOT NULL CHECK (amount_pence > 0)
);
"""


@dataclass(frozen=True)
class Transaction:
    id: int
    type: str
    amount_pence: int
    category: str
    tx_date: str
    note: str


class Database:
    def __init__(self, path: str):
        if path != ":memory:":
            resolved = Path(path).expanduser()
            resolved.parent.mkdir(parents=True, exist_ok=True)
            path = str(resolved)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # --- transactions -------------------------------------------------
    def add_transaction(self, tx_type, amount_pence, category, tx_date, note="") -> int:
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO transactions (type, amount_pence, category, tx_date, note) "
                "VALUES (?, ?, ?, ?, ?)",
                (tx_type, amount_pence, category, tx_date, note),
            )
        return cur.lastrowid

    def add_many(self, rows: Iterable[tuple]) -> int:
        """Insert many rows in a single transaction (all-or-nothing)."""
        rows = list(rows)
        with self.conn:
            self.conn.executemany(
                "INSERT INTO transactions (type, amount_pence, category, tx_date, note) "
                "VALUES (?, ?, ?, ?, ?)",
                rows,
            )
        return len(rows)

    def delete_transaction(self, tx_id: int) -> bool:
        with self.conn:
            cur = self.conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        return cur.rowcount == 1

    def list_transactions(
        self,
        month: Optional[str] = None,
        category: Optional[str] = None,
        tx_type: Optional[str] = None,
    ) -> list:
        sql = "SELECT * FROM transactions WHERE 1=1"
        params: list = []
        if month:
            sql += " AND substr(tx_date, 1, 7) = ?"
            params.append(month)
        if category:
            sql += " AND category = ?"
            params.append(category)
        if tx_type:
            sql += " AND type = ?"
            params.append(tx_type)
        sql += " ORDER BY tx_date, id"
        return [Transaction(**dict(r)) for r in self.conn.execute(sql, params)]

    # --- budgets ------------------------------------------------------
    def set_budget(self, category: str, amount_pence: int) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO budgets (category, amount_pence) VALUES (?, ?) "
                "ON CONFLICT(category) DO UPDATE SET amount_pence = excluded.amount_pence",
                (category, amount_pence),
            )

    def remove_budget(self, category: str) -> bool:
        with self.conn:
            cur = self.conn.execute("DELETE FROM budgets WHERE category = ?", (category,))
        return cur.rowcount == 1

    def get_budgets(self) -> dict:
        return {
            r["category"]: r["amount_pence"]
            for r in self.conn.execute(
                "SELECT category, amount_pence FROM budgets ORDER BY category"
            )
        }
