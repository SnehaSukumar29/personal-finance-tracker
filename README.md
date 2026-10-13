# Python Finance Tracker

![tests](https://github.com/SnehaSukumar29/personal-finance-tracker/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A command-line personal finance tracker for logging income and expenses, setting monthly category budgets and producing budget-vs-actual reports. It is built only on the Python standard library (SQLite, `argparse`, `csv`, `decimal`) and was written with secure coding practices in mind: parameterised SQL, strict input validation, CSV formula-injection protection and all-or-nothing imports.

## Features

- Add, list, filter and delete income and expense transactions
- Monthly category budgets with **OK / WARNING (80%+) / OVER** status
- Monthly report: income, expenses, net and savings rate
- CSV export and import, with validation of every row before anything is saved
- Installs as a real `finance-tracker` command; data stored locally in SQLite
- 26 unit tests, run automatically on Windows and Linux via GitHub Actions

## Demo

```text
$ finance-tracker import sample_data/october_2026.csv
Imported 12 transaction(s) from sample_data/october_2026.csv.

$ finance-tracker budget set groceries 220
$ finance-tracker budget set "eating out" 60
$ finance-tracker budget set transport 50

$ finance-tracker report --month 2026-10
Monthly report - 2026-10
============================================================
Income:        £2,220.00
Expenses:      £1,006.84
Net:           £1,213.16
Savings rate: 54.6%

Category                   Spent        Budget     Used  Status
------------------------------------------------------------
eating out                £66.00        £60.00   110.0%  OVER
groceries                £237.35       £220.00   107.9%  OVER
rent                     £650.00             -        -  NO BUDGET
subscriptions              £9.99             -        -  NO BUDGET
transport                 £43.50        £50.00    87.0%  WARNING
```

## Installation

Requires Python 3.9 or later. No third-party packages are needed.

```bash
git clone https://github.com/SnehaSukumar29/personal-finance-tracker.git
cd personal-finance-tracker
python -m pip install .
```

You can also run it without installing: `python -m finance_tracker <command>`.

## Usage

| Command | What it does |
|---|---|
| `finance-tracker add expense 12.50 groceries --date 2026-10-03 --note "Weekly shop"` | Add a transaction (date defaults to today) |
| `finance-tracker add income 2100 salary` | Add income |
| `finance-tracker list --month 2026-10 --category groceries` | List with optional filters (`--month`, `--category`, `--type`) |
| `finance-tracker delete 7` | Delete transaction #7 |
| `finance-tracker budget set groceries 220` | Set or update a monthly budget |
| `finance-tracker budget list` / `budget remove groceries` | View or remove budgets |
| `finance-tracker report --month 2026-10` | Monthly summary (defaults to current month) |
| `finance-tracker export october.csv --month 2026-10` | Export to CSV |
| `finance-tracker import october.csv` | Import from CSV (columns: `date,type,amount,category,note`) |

By default data is stored in `~/.finance_tracker/finance.db`. Use `--db PATH` or set the `FINANCE_DB` environment variable to use a different file.

## Security and design decisions

| Risk | How it is handled |
|---|---|
| SQL injection (CWE-89) | Every query uses `?` parameter binding; user input is never concatenated into SQL. A unit test confirms an injection payload is treated as plain data. |
| CSV / formula injection (CWE-1236) | On export, any text cell starting with `=`, `+`, `-`, `@`, tab or carriage return is prefixed with `'` so spreadsheet software shows it as text instead of running it. The prefix is removed again on import so files round-trip cleanly. |
| Invalid or malicious input | Amounts, dates, months, categories and notes are validated before use. Categories use an allow-list pattern, notes are length-limited and have control characters (e.g. terminal escape sequences) stripped. |
| Partial or corrupt imports | The whole CSV is validated first; if any row is invalid, nothing is saved and every error is reported with its line number. Imports are capped at 10,000 rows. |
| Database integrity | SQLite `CHECK` constraints enforce positive amounts and valid types as a second layer of defence behind application validation. |
| Money rounding errors | Amounts are stored as integer pence using `Decimal` parsing, never floats, so `0.10 + 0.20` is exactly `0.30`. |

## Project structure

```text
finance_tracker/
├── cli.py          # argparse command-line interface
├── db.py           # SQLite storage layer (parameterised queries)
├── money.py        # amount parsing and formatting in integer pence
├── validation.py   # input validation helpers
├── reports.py      # monthly report and budget status logic
└── csv_io.py       # CSV export (formula-injection safe) and validated import
tests/              # unittest suite (26 tests)
sample_data/        # example month of transactions
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

## Possible future improvements

- Recurring transactions (e.g. rent, subscriptions)
- Charts of spending by category over time
- Optional encryption of the database file at rest

## Licence

MIT. See [LICENSE](LICENSE).
