from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import litellm
import json
import os
import sqlite3
import datetime
import speech_recognition as sr
import shutil
# import pandas as pd # Removed for zero-dependency

# TinyDB — embedded NoSQL (no server needed)
from tinydb import TinyDB, Query as TinyQuery

# ─────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────
MODEL_NAME         = "ollama/minimax-m2:cloud"
ANALYST_MODEL_NAME = "ollama/minimax-m2:cloud"
AUDIT_LOG_FILE     = "audit_log.json"

BASE_DIR       = os.path.dirname(__file__)
SQLITE_DB_PATH = os.path.join(BASE_DIR, "company_sql.db")
TINYDB_PATH    = os.path.join(BASE_DIR, "company_nosql.json")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────
# SHARED SEED DATA  (used by both databases)
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

SCHEMA_DESC = """
Fields (same in both SQL and NoSQL):
  name            (str)   – employee name
  age             (int)   – age in years
  department      (str)   – IT | HR | Finance | Marketing
  salary_amount   (float) – monthly salary in INR
  salary_currency (str)   – always "INR"
  location        (str)   – city
"""

# ─────────────────────────────────────────────────
# TinyDB — embedded NoSQL setup
# ─────────────────────────────────────────────────
# Check BEFORE TinyDB creates the file
_tinydb_is_new = not os.path.exists(TINYDB_PATH)
tinydb_conn = TinyDB(TINYDB_PATH)
employees_table = tinydb_conn.table("employees")

def init_tinydb():
    if _tinydb_is_new:
        employees_table.insert_multiple(SEED_EMPLOYEES)
        print(f"✅ TinyDB created & seeded ({len(SEED_EMPLOYEES)} docs) → {TINYDB_PATH}")
    else:
        print(f"ℹ️  TinyDB loaded — {len(employees_table)} docs in table (no seeding)")

init_tinydb()

# ─────────────────────────────────────────────────
# SQLite — embedded SQL setup
# ─────────────────────────────────────────────────
def init_sqlite():
    file_is_new = not os.path.exists(SQLITE_DB_PATH)
    con = sqlite3.connect(SQLITE_DB_PATH)
    cur = con.cursor()

    # Detect & migrate old schema (single 'salary' column)
    cur.execute("PRAGMA table_info(employees)")
    cols = [r[1] for r in cur.fetchall()]
    if cols and "salary_amount" not in cols:
        print("⚠️  Old SQLite schema — dropping and recreating.")
        cur.execute("DROP TABLE IF EXISTS employees")
        file_is_new = True   # force seed after recreation

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            age             INTEGER NOT NULL,
            department      TEXT    NOT NULL,
            salary_amount   REAL    NOT NULL,
            salary_currency TEXT    NOT NULL DEFAULT 'INR',
            location        TEXT    NOT NULL
        )
    """)

    if file_is_new:
        rows = [(e["name"], e["age"], e["department"],
                 e["salary_amount"], e["salary_currency"], e["location"])
                for e in SEED_EMPLOYEES]
        cur.executemany(
            "INSERT INTO employees (name,age,department,salary_amount,salary_currency,location) "
            "VALUES (?,?,?,?,?,?)", rows
        )
        print(f"✅ SQLite created & seeded ({len(rows)} rows) → {SQLITE_DB_PATH}")
    else:
        cur.execute("SELECT COUNT(*) FROM employees")
        count = cur.fetchone()[0]
        print(f"ℹ️  SQLite loaded — {count} rows (no seeding)")

    con.commit()
    con.close()

init_sqlite()

def get_sqlite_con():
    con = sqlite3.connect(SQLITE_DB_PATH)
    con.row_factory = sqlite3.Row
    return con

# ─────────────────────────────────────────────────
# Schema helpers
# ─────────────────────────────────────────────────
def get_tinydb_schema():
    if len(employees_table) == 0:
        return SCHEMA_DESC
    sample = employees_table.all()[0]
    return json.dumps({k: type(v).__name__ for k, v in sample.items()}, indent=2)

def get_sqlite_schema():
    try:
        con = get_sqlite_con()
        cur = con.cursor()
        cur.execute("PRAGMA table_info(employees)")
        cols = cur.fetchall()
        con.close()
        return json.dumps({r["name"]: r["type"] for r in cols}, indent=2)
    except Exception as e:
        return f"Error: {e}"

# ─────────────────────────────────────────────────
# TinyDB filter translator  (MongoDB-style JSON → TinyDB)
# ─────────────────────────────────────────────────
def _build_tinydb_cond(field: str, spec, Q):
    """Translate one field's filter spec into a TinyDB condition."""
    if isinstance(spec, dict):
        conds = []
        for op, val in spec.items():
            f = getattr(Q, field)
            if op == "$gt":   conds.append(f > val)
            elif op == "$gte": conds.append(f >= val)
            elif op == "$lt":  conds.append(f < val)
            elif op == "$lte": conds.append(f <= val)
            elif op == "$ne":  conds.append(f != val)
            elif op == "$in":  conds.append(f.one_of(val))
            elif op == "$nin": conds.append(~f.one_of(val))
            elif op == "$regex":
                import re
                conds.append(f.matches(val, flags=re.IGNORECASE))
        result = conds[0]
        for c in conds[1:]:
            result &= c
        return result
    else:
        # Plain equality
        return getattr(Q, field) == spec

# ─────────────────────────────────────────────────
# TinyDB Smart Update Helper
# ─────────────────────────────────────────────────
def apply_smart_update(doc: dict, update_spec: dict):
    """Applies mutations to a document, handling arithmetic operators."""
    for field, val in update_spec.items():
        if isinstance(val, dict):
            # Handle Mongo-style operators
            current = doc.get(field, 0)
            if "$inc" in val:
                doc[field] = current + val["$inc"]
            elif "$mul" in val:
                doc[field] = current * val["$mul"]
            elif "$expr" in val:
                # Handle "lambda current: current * 1.1" or "current * 1.1"
                expr_str = str(val["$expr"])
                try:
                    # Basic safe evaluation for math-only expressions
                    if "lambda" in expr_str:
                        # Extract the expression after the colon
                        calc_part = expr_str.split(":", 1)[1].strip()
                    else:
                        calc_part = expr_str
                    
                    # Clean the expression (strip "int(", etc. if LLM added them)
                    calc_part = calc_part.replace("int(", "").replace(")", "").strip()
                    
                    # Compute using eval with restricted globals/locals
                    new_val = eval(calc_part, {"__builtins__": {}}, {"current": current})
                    doc[field] = new_val
                except Exception as e:
                    print(f"Error evaluating $expr {expr_str!r}: {e}")
                    doc[field] = val["$expr"] # Fallback
        else:
            # Regular literal update
            doc[field] = val
    return doc

def tinydb_filter(filter_dict: dict):
    """Convert a MongoDB-style filter dict to a TinyDB condition (or None for all docs)."""
    if not filter_dict:
        return None
    Q = TinyQuery()
    conditions = [_build_tinydb_cond(f, v, Q) for f, v in filter_dict.items()]
    # Filter out None conditions
    conditions = [c for c in conditions if c is not None]
    if not conditions:
        return None
    result = conditions[0]
    for c in conditions[1:]:
        result &= c
    return result

# ─────────────────────────────────────────────────
# LLM helpers
# ─────────────────────────────────────────────────
def _call_llm(prompt: str) -> str:
    """Call the LLM and return the cleaned text content."""
    print(f"  [LLM] Calling model {MODEL_NAME}...")
    try:
        response = litellm.completion(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            timeout=30  # Prevent infinite hangs
        )
        res = response.choices[0].message.content
        print(f"  [LLM] Success. Length: {len(res)}")
    except Exception as e:
        print(f"  [LLM] Error: {e}")
        raise # Re-raise the exception after logging
    
    # Strip markdown fences
    content = res.strip()
    for fence in ("```json", "```sql", "```python", "```"):
        if fence in content:
            parts = content.split(fence)
            if len(parts) >= 3:
                content = parts[1].split("```")[0].strip()
            break
    return content

def generate_nosql_query(nl_query: str, schema: str, mode: str) -> dict:
    """LLM → MongoDB-style JSON filter/mutation for TinyDB."""
    if mode == "mutation":
        task = """
Return JSON with:
  "method": "insert" | "update" | "delete"
  "filter": {} (for update/delete — which docs to target)
  "update": {} (for update — the new field values, flat dict)
  "document": {} (for insert — the new document fields)
"""
    else:
        task = """
Return a MongoDB-style read query JSON:
{
  "filter": {},          // field conditions — use $gt, $lt, $gte, $lte, $ne, $in, $regex
  "sort": "field_name"   // optional
}
"""
    prompt = f"""You are a NoSQL assistant for TinyDB (document database).
Schema:
{schema}

Task: {task}

User request: "{nl_query}"

Return ONLY valid JSON. No markdown. No explanation."""
    try:
        content = _call_llm(prompt)
        return json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NoSQL LLM error: {e}")


def generate_sql_query(nl_query: str, schema: str, mode: str) -> str:
    """LLM → SQL SELECT or mutation statement for SQLite."""
    if mode == "mutation":
        task = """Generate a single SQLite DML statement: INSERT INTO, UPDATE ... SET ... WHERE, or DELETE FROM ... WHERE.
Return ONLY the SQL. No markdown."""
    else:
        task = """Generate a single SQLite SELECT statement.
Return ONLY the SQL. No markdown."""

    prompt = f"""You are a SQLite SQL expert.
Table: employees
Schema (column → type):
{schema}

Task: {task}

User request: "{nl_query}"

SQL:"""
    try:
        return _call_llm(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL LLM error: {e}")


def generate_insights(results: list, nl_query: str) -> str:
    if not results:
        return ""
    try:
        # Simple summary instead of pandas describe()
        count = len(results)
        sample = results[:2]
        prompt = f"""You are a Data Analyst.
User Query: "{nl_query}"
Data Results Count: {count}
Sample Data: {json.dumps(sample)}

Provide 3 concise bullet-point insights. Focus only on the data."""
        return _call_llm(prompt)
    except Exception as e:
        return f"Could not generate insights: {e}"


# ─────────────────────────────────────────────────
# Audit
# ─────────────────────────────────────────────────
def log_audit(user, action, query, status, db_type=None, snapshot=None):
    global audit_log, audit_id_counter
    entry = {
        "id": audit_id_counter,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "query": str(query),
        "status": status,
        "db_type": db_type,
        "snapshot": snapshot,
        "undone": False
    }
    audit_id_counter += 1
    audit_log.append(entry)
    
    # Still write to file for persistence
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            # We don't write snapshots to the file to keep it small in this demo
            file_entry = entry.copy()
            file_entry.pop("snapshot", None)
            f.write(json.dumps(file_entry) + "\n")
    except:
        pass
        
    return entry


# ─────────────────────────────────────────────────
# Pydantic request model
# ─────────────────────────────────────────────────
# -----------------------------
# Global State for Demo
# -----------------------------
# In a real app, use a DB table. For demo, we use session-like global list.
# Each entry: {id, timestamp, user, action, query, status, db_type, snapshot, undone}
audit_log = []
audit_id_counter = 0

class QueryRequest(BaseModel):
    prompt: str
    role: str    = "Viewer"   # "Admin" | "Viewer"
    mode: str    = "query"    # "query" | "mutation"
    db_type: str = "nosql"    # "nosql" (TinyDB) | "sql" (SQLite)


# ─────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "nosql": f"TinyDB → {TINYDB_PATH}",
        "sql":   f"SQLite → {SQLITE_DB_PATH}",
    }

@app.get("/api/schema")
def get_schema(db_type: str = "nosql"):
    if db_type == "sql":
        return {"db_type": "sql",   "schema": get_sqlite_schema(), "source": "SQLite · employees"}
    return     {"db_type": "nosql", "schema": get_tinydb_schema(), "source": "TinyDB · employees"}

@app.get("/api/audit")
def get_audit():
    # Return reversed to show latest first
    return audit_log[::-1]

@app.post("/api/audit/undo/{log_id}")
async def undo_action(log_id: int):
    global audit_log
    entry = next((item for item in audit_log if item["id"] == log_id), None)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Log entry not found")
    if entry["undone"]:
        raise HTTPException(status_code=400, detail="Action already undone")
    if not entry.get("snapshot"):
        raise HTTPException(status_code=400, detail="No snapshot available for this action")

    try:
        if entry["db_type"] == "sql":
            con = get_sqlite_con()
            cur = con.cursor()
            # Clear table and restore from snapshot
            cur.execute("DELETE FROM employees")
            for row in entry["snapshot"]:
                fields = ", ".join(row.keys())
                placeholders = ", ".join(["?"] * len(row))
                cur.execute(f"INSERT INTO employees ({fields}) VALUES ({placeholders})", list(row.values()))
            con.commit()
            con.close()
        else:
            table = get_tinydb_table()
            # Restore documents by doc_id
            for doc_data in entry["snapshot"]:
                doc_id = doc_data.pop("__doc_id__", None)
                if doc_id:
                    table.update(doc_data, doc_ids=[doc_id])
        
        entry["undone"] = True
        return {"message": "Action undone successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Undo failed: {e}")

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        with open("temp_audio.wav", "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        r = sr.Recognizer()
        with sr.AudioFile("temp_audio.wav") as src:
            text = r.recognize_google(r.record(src))
            return {"transcription": text}
    except Exception as e:
        return {"error": str(e)}


# ─── Main query endpoint ────────────────────────
@app.post("/api/query")
def run_query(req: QueryRequest):
    print(f"[Query] prompt={req.prompt!r}  role={req.role}  mode={req.mode}  db={req.db_type}")

    # RBAC
    if req.mode == "mutation" and req.role != "Admin":
        log_audit(req.role, "Query", req.prompt, "Failed – Permission Denied")
        return {"error": "You do not have permission to perform mutations."}

    # ══════════════════════════════════════════════
    # NoSQL path  (TinyDB — embedded, file-based)
    # ══════════════════════════════════════════════
    if req.db_type == "nosql":
        schema = get_tinydb_schema()

        try:
            query_obj = generate_nosql_query(req.prompt, schema, req.mode)
            log_audit(req.role, "Generate NoSQL Query", req.prompt, "Success")
        except Exception as e:
            log_audit(req.role, "Generate NoSQL Query", req.prompt, f"Failed: {e}")
            return {"error": str(e), "step": "LLM Generation"}

        try:
            # ── READ ──────────────────────────────
            if req.mode == "query":
                flt = query_obj.get("filter", {})
                cond = tinydb_filter(flt)
                if cond is None:
                    docs = employees_table.all()
                else:
                    docs = employees_table.search(cond)

                # Optional sort
                sort_field = query_obj.get("sort")
                if sort_field and docs:
                    docs = sorted(docs, key=lambda d: d.get(sort_field, ""))

                results = [dict(d) for d in docs]
                insights = generate_insights(results, req.prompt) if results else ""
                log_audit(req.role, "Execute NoSQL Query", str(query_obj), "Success")
                return {
                    "status": "success", "db_type": "nosql", "db_label": "TinyDB",
                    "generated_query": query_obj,
                    "results": results, "count": len(results), "insights": insights,
                }

            # ── MUTATION ──────────────────────────
            else:
                method = query_obj.get("method", "")
                flt    = query_obj.get("filter", {})
                cond   = tinydb_filter(flt)

                if method == "insert":
                    doc = query_obj.get("document", {})
                    employees_table.insert(doc)
                    msg = f"Inserted 1 document."

                elif method == "update":
                    upd = query_obj.get("update", {})
                    
                    # Fetch docs to update
                    if cond is None:
                        target_docs = employees_table.all()
                    else:
                        target_docs = employees_table.search(cond)
                    
                    # Apply smart update to each and save
                    snapshot = []
                    for doc in target_docs:
                        doc_id = doc.doc_id
                        snapshot.append(dict(doc) | {"__doc_id__": doc_id})
                        new_doc = apply_smart_update(dict(doc), upd)
                        employees_table.update(new_doc, doc_ids=[doc_id])
                    
                    msg = f"Updated {len(target_docs)} documents."

                elif method == "delete":
                    if cond is None:
                        # Fetch snapshot before trunacting
                        snapshot_docs = employees_table.all()
                        snapshot = [dict(d) | {"__doc_id__": d.doc_id} for d in snapshot_docs]
                        employees_table.truncate()
                        msg = "All documents deleted."
                    else:
                        target_docs = employees_table.search(cond)
                        snapshot = [dict(d) | {"__doc_id__": d.doc_id} for d in target_docs]
                        employees_table.remove(cond)
                        msg = "Matching documents deleted."
                else:
                    return {"error": f"Unknown method: {method!r}"}

                log_audit(req.role, "NoSQL Mutation", str(query_obj), "Success", db_type="nosql", snapshot=snapshot)
                return {"status": "success", "db_type": "nosql", "db_label": "TinyDB",
                        "generated_query": query_obj, "message": msg,
                        "results": [], "count": 0, "insights": ""}

        except Exception as e:
            log_audit(req.role, "Execute NoSQL Query", str(query_obj), f"Failed: {e}")
            return {"error": str(e), "step": "TinyDB Execution"}

    # ══════════════════════════════════════════════
    # SQL path  (SQLite — embedded, file-based)
    # ══════════════════════════════════════════════
    elif req.db_type == "sql":
        schema = get_sqlite_schema()

        try:
            sql = generate_sql_query(req.prompt, schema, req.mode)
            log_audit(req.role, "Generate SQL", req.prompt, "Success")
        except Exception as e:
            log_audit(req.role, "Generate SQL", req.prompt, f"Failed: {e}")
            return {"error": str(e), "step": "LLM SQL Generation"}

        try:
            con = get_sqlite_con()
            cur = con.cursor()

            # ── READ ──────────────────────────────
            if req.mode == "query":
                cur.execute(sql)
                rows = cur.fetchall()
                con.close()
                results = [dict(r) for r in rows]
                insights = generate_insights(results, req.prompt) if results else ""
                log_audit(req.role, "Execute SQL", sql, "Success")
                return {
                    "status": "success", "db_type": "sql", "db_label": "SQLite",
                    "generated_query": {"sql": sql},
                    "results": results, "count": len(results), "insights": insights,
                }

            # ── MUTATION ──────────────────────────
            else:
                # Capture snapshot for SQL Undo (Zero-dependency)
                cur.execute("SELECT * FROM employees")
                snapshot = [dict(r) for r in cur.fetchall()]

                cur.execute(sql)
                affected = cur.rowcount
                con.commit()
                con.close()
                action  = sql.strip().split()[0].upper()
                log_audit(req.role, "SQL Mutation", sql, "Success", db_type="sql", snapshot=snapshot)
                return {
                    "status": "success", "db_type": "sql", "db_label": "SQLite",
                    "generated_query": {"sql": sql},
                    "message": f"{action} executed — {affected} row(s) affected.",
                    "results": [], "count": 0, "insights": "",
                }

        except Exception as e:
            log_audit(req.role, "Execute SQL", sql, f"Failed: {e}")
            return {"error": str(e), "step": "SQLite Execution"}

    else:
        return {"error": f"Unknown db_type: {req.db_type!r}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
