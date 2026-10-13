"""Command-line interface."""
import argparse
import os
import sys
from datetime import date

from finance_tracker import __version__
from finance_tracker.csv_io import CsvImportError, export_csv, import_csv
from finance_tracker.db import Database
from finance_tracker.money import format_pence, parse_amount
from finance_tracker.reports import build_monthly_report
from finance_tracker.validation import (
    validate_category,
    validate_date,
    validate_month,
    validate_note,
    validate_type,
)

DEFAULT_DB = os.path.join("~", ".finance_tracker", "finance.db")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="finance-tracker",
        description="Track income, expenses and monthly budgets from the command line.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument(
        "--db",
        default=os.environ.get("FINANCE_DB", DEFAULT_DB),
        help="SQLite database path (default: %(default)s, or $FINANCE_DB)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add an income or expense")
    add.add_argument("type", choices=["income", "expense"])
    add.add_argument("amount", help="Amount in pounds, e.g. 12.50")
    add.add_argument("category", help="e.g. groceries, rent, salary")
    add.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD (default: today)")
    add.add_argument("--note", default="", help="Optional note (max 200 chars)")

    ls = sub.add_parser("list", help="List transactions")
    ls.add_argument("--month", help="YYYY-MM")
    ls.add_argument("--category")
    ls.add_argument("--type", choices=["income", "expense"])

    rm = sub.add_parser("delete", help="Delete a transaction by ID")
    rm.add_argument("id", type=int)

    bud = sub.add_parser("budget", help="Manage monthly category budgets")
    bsub = bud.add_subparsers(dest="budget_command", required=True)
    bset = bsub.add_parser("set", help="Set a monthly budget for a category")
    bset.add_argument("category")
    bset.add_argument("amount")
    brm = bsub.add_parser("remove", help="Remove a category budget")
    brm.add_argument("category")
    bsub.add_parser("list", help="Show all budgets")

    rep = sub.add_parser("report", help="Monthly summary with budget status")
    rep.add_argument("--month", default=date.today().strftime("%Y-%m"), help="YYYY-MM (default: this month)")

    exp = sub.add_parser("export", help="Export transactions to CSV")
    exp.add_argument("file")
    exp.add_argument("--month", help="YYYY-MM")

    imp = sub.add_parser("import", help="Import transactions from CSV")
    imp.add_argument("file")
    return p


def _print_transactions(rows) -> None:
    if not rows:
        print("No transactions found.")
        return
    print(f"{'ID':>4}  {'Date':<10}  {'Type':<7}  {'Amount':>12}  {'Category':<18}  Note")
    print("-" * 72)
    for tx in rows:
        print(
            f"{tx.id:>4}  {tx.tx_date:<10}  {tx.type:<7}  "
            f"{format_pence(tx.amount_pence):>12}  {tx.category:<18}  {tx.note}"
        )


def _print_report(report) -> None:
    print(f"Monthly report - {report.month}")
    print("=" * 60)
    print(f"Income:   {format_pence(report.income_pence):>14}")
    print(f"Expenses: {format_pence(report.expense_pence):>14}")
    print(f"Net:      {format_pence(report.net_pence):>14}")
    rate = report.savings_rate
    print(f"Savings rate: {'n/a' if rate is None else f'{rate}%'}")
    if report.lines:
        print()
        print(f"{'Category':<18}  {'Spent':>12}  {'Budget':>12}  {'Used':>7}  Status")
        print("-" * 60)
        for line in report.lines:
            budget = "-" if line.budget_pence is None else format_pence(line.budget_pence)
            used = "-" if line.percent_used is None else f"{line.percent_used}%"
            print(
                f"{line.category:<18}  {format_pence(line.spent_pence):>12}  "
                f"{budget:>12}  {used:>7}  {line.status}"
            )


def run(args, db: Database) -> int:
    if args.command == "add":
        tx_id = db.add_transaction(
            validate_type(args.type),
            parse_amount(args.amount),
            validate_category(args.category),
            validate_date(args.date),
            validate_note(args.note),
        )
        print(f"Added transaction #{tx_id}.")
    elif args.command == "list":
        _print_transactions(db.list_transactions(
            month=validate_month(args.month) if args.month else None,
            category=validate_category(args.category) if args.category else None,
            tx_type=args.type,
        ))
    elif args.command == "delete":
        if not db.delete_transaction(args.id):
            print(f"No transaction with ID {args.id}.", file=sys.stderr)
            return 1
        print(f"Deleted transaction #{args.id}.")
    elif args.command == "budget":
        if args.budget_command == "set":
            category = validate_category(args.category)
            db.set_budget(category, parse_amount(args.amount))
            print(f"Budget for '{category}' set to {format_pence(parse_amount(args.amount))}/month.")
        elif args.budget_command == "remove":
            category = validate_category(args.category)
            if not db.remove_budget(category):
                print(f"No budget set for '{category}'.", file=sys.stderr)
                return 1
            print(f"Removed budget for '{category}'.")
        else:
            budgets = db.get_budgets()
            if not budgets:
                print("No budgets set.")
            for cat, pence in budgets.items():
                print(f"{cat:<18}  {format_pence(pence):>12}")
    elif args.command == "report":
        _print_report(build_monthly_report(db, validate_month(args.month)))
    elif args.command == "export":
        count = export_csv(db, args.file, validate_month(args.month) if args.month else None)
        print(f"Exported {count} transaction(s) to {args.file}.")
    elif args.command == "import":
        count = import_csv(db, args.file)
        print(f"Imported {count} transaction(s) from {args.file}.")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    db = Database(args.db)
    try:
        return run(args, db)
    except CsvImportError as exc:
        print("Import cancelled - no rows were saved:", file=sys.stderr)
        for err in exc.errors:
            print(f"  {err}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()
