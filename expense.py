"""Expense tracker: SQLite + command-line menu.

Run: python expense_tracker.py
Concepts: sqlite3, functions, input validation, SQL aggregation.
"""
import sqlite3
from datetime import date

DB_FILE = "expenses.db"


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spent_on TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL
        )"""
    )
    return conn


def ask_amount(prompt):
    while True:
        try:
            value = float(input(prompt))
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("Please enter a positive number.")


def ask_date(prompt):
    while True:
        raw = input(f"{prompt} [YYYY-MM-DD, Enter = today]: ").strip()
        if not raw:
            return date.today().isoformat()
        try:
            return date.fromisoformat(raw).isoformat()
        except ValueError:
            print("Use the format YYYY-MM-DD.")


def print_rows(rows):
    if not rows:
        print("No expenses found.")
        return
    print(f"\n{'ID':<4} {'Date':<11} {'Category':<14} {'Description':<22} {'Amount':>10}")
    print("-" * 65)
    total = 0
    for r in rows:
        print(f"{r['id']:<4} {r['spent_on']:<11} {r['category']:<14} "
              f"{(r['description'] or '')[:21]:<22} {r['amount']:>10.2f}")
        total += r["amount"]
    print("-" * 65)
    print(f"{'Total':<53} {total:>10.2f}\n")


def add_expense(conn):
    spent_on = ask_date("Date")
    category = input("Category (e.g. food, transport): ").strip().lower() or "other"
    description = input("Description: ").strip()
    amount = ask_amount("Amount: ")
    conn.execute(
        "INSERT INTO expenses (spent_on, category, description, amount) VALUES (?, ?, ?, ?)",
        (spent_on, category, description, amount),
    )
    conn.commit()
    print("Expense added.")


def list_expenses(conn):
    category = input("Filter by category (Enter = all): ").strip().lower()
    month = input("Filter by month YYYY-MM (Enter = all): ").strip()
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if month:
        query += " AND substr(spent_on, 1, 7) = ?"
        params.append(month)
    query += " ORDER BY spent_on DESC, id DESC"
    print_rows(conn.execute(query, params).fetchall())


def pick_expense(conn):
    try:
        expense_id = int(input("Expense ID: "))
    except ValueError:
        print("ID must be a number.")
        return None
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if row is None:
        print("No expense with that ID.")
    return row


def edit_expense(conn):
    row = pick_expense(conn)
    if row is None:
        return
    print("Press Enter to keep the current value.")
    category = input(f"Category [{row['category']}]: ").strip().lower() or row["category"]
    description = input(f"Description [{row['description']}]: ").strip() or row["description"]
    raw_amount = input(f"Amount [{row['amount']}]: ").strip()
    try:
        amount = float(raw_amount) if raw_amount else row["amount"]
    except ValueError:
        print("Invalid amount, keeping the old one.")
        amount = row["amount"]
    conn.execute(
        "UPDATE expenses SET category = ?, description = ?, amount = ? WHERE id = ?",
        (category, description, amount, row["id"]),
    )
    conn.commit()
    print("Expense updated.")


def delete_expense(conn):
    row = pick_expense(conn)
    if row is None:
        return
    if input(f"Delete '{row['description']}' ({row['amount']:.2f})? [y/N]: ").lower() == "y":
        conn.execute("DELETE FROM expenses WHERE id = ?", (row["id"],))
        conn.commit()
        print("Deleted.")


def monthly_summary(conn):
    rows = conn.execute(
        """SELECT substr(spent_on, 1, 7) AS month, category, SUM(amount) AS total
           FROM expenses GROUP BY month, category ORDER BY month DESC, total DESC"""
    ).fetchall()
    if not rows:
        print("Nothing to summarise yet.")
        return
    current = None
    for r in rows:
        if r["month"] != current:
            current = r["month"]
            month_total = conn.execute(
                "SELECT SUM(amount) FROM expenses WHERE substr(spent_on, 1, 7) = ?",
                (current,),
            ).fetchone()[0]
            print(f"\n== {current}  (total {month_total:.2f}) ==")
        print(f"  {r['category']:<14} {r['total']:>10.2f}")
    print()


MENU = """
1) Add expense
2) List / filter expenses
3) Edit expense
4) Delete expense
5) Monthly summary
6) Quit
"""


def main():
    conn = get_conn()
    actions = {
        "1": add_expense,
        "2": list_expenses,
        "3": edit_expense,
        "4": delete_expense,
        "5": monthly_summary,
    }
    while True:
        print(MENU)
        choice = input("Choose: ").strip()
        if choice == "6":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action:
            action(conn)
        else:
            print("Invalid choice.")
    conn.close()


if __name__ == "__main__":
    main()
            
