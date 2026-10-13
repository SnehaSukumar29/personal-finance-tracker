"""Monthly summary and budget-vs-actual reporting."""
from dataclasses import dataclass, field
from typing import Optional

from finance_tracker.db import Database

WARN_THRESHOLD = 0.8  # flag categories at 80% or more of budget


@dataclass
class CategoryLine:
    category: str
    spent_pence: int
    budget_pence: Optional[int]

    @property
    def status(self) -> str:
        if self.budget_pence is None:
            return "NO BUDGET"
        if self.spent_pence > self.budget_pence:
            return "OVER"
        if self.spent_pence >= self.budget_pence * WARN_THRESHOLD:
            return "WARNING"
        return "OK"

    @property
    def percent_used(self) -> Optional[float]:
        if not self.budget_pence:
            return None
        return round(self.spent_pence / self.budget_pence * 100, 1)


@dataclass
class MonthlyReport:
    month: str
    income_pence: int = 0
    expense_pence: int = 0
    lines: list = field(default_factory=list)

    @property
    def net_pence(self) -> int:
        return self.income_pence - self.expense_pence

    @property
    def savings_rate(self) -> Optional[float]:
        if self.income_pence == 0:
            return None
        return round(self.net_pence / self.income_pence * 100, 1)


def build_monthly_report(db: Database, month: str) -> MonthlyReport:
    report = MonthlyReport(month=month)
    spent: dict = {}
    for tx in db.list_transactions(month=month):
        if tx.type == "income":
            report.income_pence += tx.amount_pence
        else:
            report.expense_pence += tx.amount_pence
            spent[tx.category] = spent.get(tx.category, 0) + tx.amount_pence

    budgets = db.get_budgets()
    for category in sorted(set(spent) | set(budgets)):
        report.lines.append(
            CategoryLine(category, spent.get(category, 0), budgets.get(category))
        )
    return report
