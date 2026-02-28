import os
import json

# ─────────────────────────────────────────────────
# DATA RECOVERY CONSTANTS
# ─────────────────────────────────────────────────
SEED_EMPLOYEES = [
    {"name": "Amit",   "age": 29, "department": "IT",        "salary_amount": 75000,  "salary_currency": "INR", "location": "Hyderabad"},
    {"name": "Priya",  "age": 24, "department": "HR",        "salary_amount": 52000,  "salary_currency": "INR", "location": "Chennai"},
    {"name": "Karan",  "age": 31, "department": "Finance",   "salary_amount": 88000,  "salary_currency": "INR", "location": "Mumbai"},
    {"name": "Neha",   "age": 27, "department": "IT",        "salary_amount": 67000,  "salary_currency": "INR", "location": "Bangalore"},
    {"name": "Raj",    "age": 35, "department": "Finance",   "salary_amount": 95000,  "salary_currency": "INR", "location": "Pune"},
    {"name": "Anita",  "age": 22, "department": "HR",        "salary_amount": 48000,  "salary_currency": "INR", "location": "Delhi"},
    {"name": "Suresh", "age": 40, "department": "IT",        "salary_amount": 110000, "salary_currency": "INR", "location": "Hyderabad"},
    {"name": "Divya",  "age": 28, "department": "Marketing", "salary_amount": 61000,  "salary_currency": "INR", "location": "Chennai"},
    {"name": "Vikram", "age": 33, "department": "Finance",   "salary_amount": 79000,  "salary_currency": "INR", "location": "Mumbai"},
    {"name": "Pooja",  "age": 26, "department": "Marketing", "salary_amount": 55000,  "salary_currency": "INR", "location": "Bangalore"},
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TINYDB_PATH = os.path.join(BASE_DIR, "backend", "company_nosql.json")

def repair_json_directly():
    print(f"--- Zero-Dependency Repair of {TINYDB_PATH} ---")
    
    if not os.path.exists(TINYDB_PATH):
        print("❌ TinyDB file not found. Nothing to repair.")
        return

    try:
        # Construct the exact TinyDB structure manually
        # TinyDB JSON: {"employees": {"1": {...}, "2": {...}}}
        
        repaired_table = {}
        for i, emp in enumerate(SEED_EMPLOYEES, 1):
            repaired_table[str(i)] = emp
            
        full_db = {"employees": repaired_table}
        
        with open(TINYDB_PATH, "w") as f:
            json.dump(full_db, f, indent=4)
            
        print(f"✅ Successfully re-wrote {TINYDB_PATH} with {len(SEED_EMPLOYEES)} numeric records.")
        
    except Exception as e:
        print(f"❌ Error during repair: {e}")

if __name__ == "__main__":
    repair_json_directly()
    print("\nRepair complete. You can now run 'python show_data.py' to check.")
