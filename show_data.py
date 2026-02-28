import sqlite3
import json
import os

# ─────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "backend", "company_sql.db")
TINYDB_PATH = os.path.join(BASE_DIR, "backend", "company_nosql.json")

def print_table(data, title):
    """Prints a list of dictionaries as a formatted table without external libs."""
    print(f"\n{'='*85}")
    print(f" {title}")
    print(f"{'='*85}")
    
    if not data:
        print("ℹ️ No records found.")
        return

    # Use all potential keys from all rows (or just the first row if strictly uniform)
    headers = []
    for row in data:
        for k in row.keys():
            if k not in headers and k != "_id": # Skip hidden IDs if any
                headers.append(k)
    
    # Calculate column widths
    widths = {h: len(h) for h in headers}
    for row in data:
        for h in headers:
            val = str(row.get(h, ""))
            widths[h] = max(widths[h], len(val))

    # Print Header
    header_row = " | ".join(h.ljust(widths[h]) for h in headers)
    print(header_row)
    print("-" * len(header_row))

    # Print Rows
    for row in data:
        row_str = " | ".join(str(row.get(h, "")).ljust(widths[h]) for h in headers)
        print(row_str)

def show_sqlite_data():
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"ℹ️ SQLite database not found at: {SQLITE_DB_PATH}")
        return

    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM employees")
        rows = [dict(r) for r in cur.fetchall()]
        print_table(rows, "SQLITE DATABASE (SQL) - employees table")
        conn.close()
    except Exception as e:
        print(f"❌ Error reading SQLite: {e}")

def show_nosql_data():
    """Reads TinyDB file directly as JSON to avoid dependency issues."""
    if not os.path.exists(TINYDB_PATH):
        print(f"ℹ️ TinyDB file not found at: {TINYDB_PATH}")
        return

    try:
        with open(TINYDB_PATH, 'r') as f:
            raw_data = json.load(f)
            # TinyDB stores data in a table named "employees" (or "_default")
            # Structure: {"employees": {"1": {...}, "2": {...}}}
            employees_dict = raw_data.get("employees", {})
            if not employees_dict:
                 # Fallback to default if not named
                 employees_dict = raw_data.get("_default", {})
                 
            data = list(employees_dict.values())
            print_table(data, "TINYDB DATABASE (NoSQL) - employees table")
    except Exception as e:
        print(f"❌ Error reading TinyDB JSON: {e}")

if __name__ == "__main__":
    print("\n" + "*"*85)
    print(" DATASENSE AI - DATA VIEWER (ZERO DEPENDENCY)")
    print("*"*85)
    show_sqlite_data()
    show_nosql_data()
    print(f"\n{'='*85}\n")
