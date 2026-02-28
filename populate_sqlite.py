import sqlite3
import json
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "backend", "company_sql.db")
TINYDB_PATH = os.path.join(BASE_DIR, "backend", "company_nosql.json")

def populate_sqlite():
    print(f"--- Populating SQLite: {SQLITE_DB_PATH} ---")
    
    if not os.path.exists(TINYDB_PATH):
        print(f"Error: Source file not found: {TINYDB_PATH}")
        return

    # 1. Read NoSQL Data
    try:
        with open(TINYDB_PATH, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            employees_dict = raw_data.get("employees", {})
            if not employees_dict:
                employees_dict = raw_data.get("_default", {})
            
            records = list(employees_dict.values())
            print(f"Success: Found {len(records)} records in JSON.")
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    # 2. Connect and Insert
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cur = conn.cursor()
        
        # Clear existing data
        cur.execute("DELETE FROM employees")
        print("Cleared existing records in 'employees' table.")
        
        insert_query = """
        INSERT INTO employees (name, age, department, salary_amount, salary_currency, location)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        for r in records:
            cur.execute(insert_query, (
                r.get("name"),
                r.get("age"),
                r.get("department"),
                r.get("salary_amount"),
                r.get("salary_currency", "INR"),
                r.get("location")
            ))
        
        conn.commit()
        print(f"Success: Successfully inserted {len(records)} records into SQLite.")
        conn.close()
    except Exception as e:
        print(f"Error updating SQLite: {e}")

if __name__ == "__main__":
    populate_sqlite()
