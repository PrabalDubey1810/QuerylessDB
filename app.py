import streamlit as st
import sqlite3
import json
import os
import pandas as pd
import plotly.express as px
import speech_recognition as sr
import io
import datetime
import litellm
from tinydb import TinyDB, Query as TinyQuery

# -----------------------------
# CONFIG
# -----------------------------
MODEL_NAME = "ollama/minimax-m2:cloud"
ANALYST_MODEL_NAME = "ollama/minimax-m2:cloud"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "backend", "company_sql.db")
TINYDB_PATH = os.path.join(BASE_DIR, "backend", "company_nosql.json")

# -----------------------------
# Database Helpers
# -----------------------------
def get_sqlite_con():
    con = sqlite3.connect(SQLITE_DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def get_tinydb_table():
    db = TinyDB(TINYDB_PATH)
    return db.table("employees")


# -----------------------------
# Helper Functions
# -----------------------------
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

def get_tinydb_schema():
    table = get_tinydb_table()
    if len(table) == 0:
        return "Schema: No documents found."
    sample = table.all()[0]
    return json.dumps({k: type(v).__name__ for k, v in sample.items()}, indent=2)

def _build_tinydb_cond(field: str, spec, Q):
    if isinstance(spec, dict):
        conds = []
        for op, val in spec.items():
            f = getattr(Q, field)
            if op == "$gt":   conds.append(f > val)
            elif op == "$gte": conds.append(f >= val)
            elif op == "$lt":  conds.append(f < val)
            elif op == "$lte": conds.append(f <= val)
            elif op == "$ne":  conds.append(f != val)
        if not conds: return None
        result = conds[0]
        for c in conds[1:]:
            result &= c
        return result
    return getattr(Q, field) == spec

def tinydb_filter(filter_dict: dict):
    if not filter_dict: return None
    Q = TinyQuery()
    conditions = []
    for f, v in filter_dict.items():
        cond = _build_tinydb_cond(f, v, Q)
        if cond: conditions.append(cond)
    if not conditions: return None
    result = conditions[0]
    for c in conditions[1:]:
        result &= c
    return result

def apply_smart_update(doc: dict, update_spec: dict):
    """Applies mutations to a doc, handling arithmetic operators like $inc, $mul, $expr."""
    for field, val in update_spec.items():
        if isinstance(val, dict):
            current = doc.get(field, 0)
            if "$inc" in val:
                doc[field] = current + val["$inc"]
            elif "$mul" in val:
                doc[field] = current * val["$mul"]
            elif "$expr" in val:
                expr_str = str(val["$expr"])
                try:
                    calc_part = expr_str.split(":", 1)[1].strip() if "lambda" in expr_str else expr_str
                    calc_part = calc_part.replace("int(", "").replace(")", "").strip()
                    doc[field] = eval(calc_part, {"__builtins__": {}}, {"current": current})
                except:
                    doc[field] = val["$expr"]
        else:
            doc[field] = val
    return doc

def undo_mutation(entry_idx):
    """Restores data from a snapshot stored in an audit log entry."""
    entry = st.session_state.audit_log[entry_idx]
    if not entry.get("snapshot") or entry.get("undone"):
        return False
    
    db_type = entry.get("db_type")
    snapshot = entry.get("snapshot")
    
    try:
        if "SQL" in db_type:
            con = get_sqlite_con()
            cur = con.cursor()
            for row in snapshot:
                # Build dynamic update to restore all fields by ID
                fields = [f for f in row.keys() if f != 'id']
                set_clause = ", ".join([f"{f} = ?" for f in fields])
                values = [row[f] for f in fields] + [row['id']]
                cur.execute(f"UPDATE employees SET {set_clause} WHERE id = ?", values)
            con.commit()
            con.close()
        else:
            table = get_tinydb_table()
            for doc_data in snapshot:
                # TinyDB snapshots stored with 'doc_id'
                doc_id = doc_data.pop("__doc_id__", None)
                if doc_id:
                    table.update(doc_data, doc_ids=[doc_id])
        
        st.session_state.audit_log[entry_idx]["undone"] = True
        return True
    except Exception as e:
        st.error(f"Undo failed: {e}")
        return False



def generate_data_story(df, user_query):
    """Generate textual insights from data snippet"""
    try:
        data_summary = df.describe(include='all').to_string()
        prompt = f"""
        You are a Data Analyst.
        
        User Query: "{user_query}"
        
        Data Summary (statistical description):
        {data_summary}
        
        Provide 3 key insights or trends from this data in concise bullet points.
        Do not explain the code. Focus on the data.
        """
        response = litellm.completion(
            model=ANALYST_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Could not generate insights: {e}"

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="DataSense AI", layout="wide")

st.title("🧠 DataSense AI - Query Assistant")
st.write("Ask questions across SQL and NoSQL data. Runs fully offline.")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    db_type = st.radio("Target Database", ["SQL (SQLite)", "NoSQL (TinyDB)"])
    
    user_role = st.selectbox("Current Role", ["Admin", "Viewer"])
    if user_role == "Viewer":
        mode_label = "🔍 Query (Read-Only)"
        st.info("Viewers are restricted to Read-Only queries.")
    else:
        mode_label = st.radio("Execution Mode", ["🔍 Query (Read-Only)", "✏️ Update (Mutations)"])
    
    mode = "mutation" if "Update" in mode_label else "query"
    
    st.divider()
    st.caption(f"Logged in as: **{user_role}**")

# Data Preview & Schema
with st.expander("📂 Database Schema"):
    if db_type == "SQL (SQLite)":
        st.write(f"Connected to **SQLite · employees**")
        st.code(get_sqlite_schema(), language="json")
    else:
        st.write(f"Connected to **TinyDB · employees**")
        st.code(get_tinydb_schema(), language="json")


# Voice Input Section
st.subheader("🎤 Voice Input")
audio_value = st.audio_input("Record your question")

if audio_value:
    # Transcribe
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_value) as source:
            audio_data = r.record(source)
            try:
                transcribed_text = r.recognize_google(audio_data)
                st.success(f"Recognized: {transcribed_text}")
                st.session_state.user_query = transcribed_text
            except sr.UnknownValueError:
                st.warning("Could not understand audio")
            except sr.RequestError as e:
                st.error(f"Could not request results; {e}")
    except Exception as e:
        st.error(f"Error processing audio: {e}")

# Audit Logging
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

def log_action(user, action, query, status):
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "query": str(query),
        "status": status
    }
    st.session_state.audit_log.append(entry)

# Audit Logging
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

def log_action(user, action, query, status, db_type=None, snapshot=None):
    """Log user actions for compliance and undo capability"""
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "query": str(query),
        "status": status,
        "db_type": db_type,
        "snapshot": snapshot,
        "undone": False
    }
    st.session_state.audit_log.append(entry)

# Chat History Initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
   pass # We render this inside the tab now

# Text Input (synced)
if 'user_query' not in st.session_state:
    st.session_state.user_query = ""

# Capture input from either voice or chat input
prompt_input = st.chat_input("Ask your question...")
if prompt_input:
    st.session_state.user_query = prompt_input

# Use voice input if present and no text input yet in this run
if audio_value and not prompt_input:
    # Logic handled in voice section, just ensuring it triggers processing
    pass

user_query = st.session_state.user_query

# -----------------------------
# LLM Interface
# -----------------------------
def generate_query(nl_query, db_type, mode, user_role):
    if db_type == "SQL (SQLite)":
        schema = get_sqlite_schema()
        task = "Generate a SQLite SELECT statement." if mode == "query" else "Generate a SQLite DML statement (INSERT/UPDATE/DELETE)."
        prompt = f"You are a SQLite expert. Table: employees. Schema: {schema}. Task: {task}. User request: \"{nl_query}\". Return ONLY SQL."
    else:
        schema = get_tinydb_schema()
        task = "Return MongoDB-style JSON filter." if mode == "query" else "Return mutation JSON with 'method', 'filter', 'update', 'document'."
        prompt = f"You are a TinyDB assistant. Schema: {schema}. Task: {task}. User request: \"{nl_query}\". Return ONLY JSON."

    response = litellm.completion(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response["choices"][0]["message"]["content"].strip()
    # Clean fences
    for fence in ["```json", "```sql", "```"]:
        if fence in content:
            content = content.split(fence)[1].split("```")[0].strip()
    return content

# -----------------------------
# Button Action
# -----------------------------
# -----------------------------
# Execution Logic
# -----------------------------
# Tabs for Enterprise Layout
tab1, tab2, tab3 = st.tabs(["💬 Chat & Analysis", "🩺 Data Quality", "📝 Audit Logs"])

with tab1:
    # Chat Interface
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Add to history
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        with st.chat_message("assistant"):
            with st.spinner(f"Generating {db_type} query..."):
                generated_output = generate_query(user_query, db_type, mode, user_role)
            
            st.markdown("### Generated Query")
            st.code(generated_output, language="sql" if "SQL" in db_type else "json")
            
            try:
                snapshot = None
                # Execution
                if db_type == "SQL (SQLite)":
                    con = get_sqlite_con()
                    if mode == "query":
                        df = pd.read_sql_query(generated_output, con)
                        results = df.to_dict('records')
                    else:
                        # Mutation Snapshot: Fetch all data before change (targeted is better but complex to parse)
                        # Given small demo size, whole table snapshot is reliable for Undo
                        snapshot_df = pd.read_sql_query("SELECT * FROM employees", con)
                        snapshot = snapshot_df.to_dict('records')
                        
                        cur = con.cursor()
                        cur.execute(generated_output)
                        con.commit()
                        st.success(f"Mutation executed: {cur.rowcount} row(s) affected.")
                        df = pd.DataFrame()
                    con.close()
                else:
                    table = get_tinydb_table()
                    query_obj = json.loads(generated_output)
                    if mode == "query":
                        flt = query_obj.get("filter", {})
                        cond = tinydb_filter(flt)
                        docs = table.search(cond) if cond else table.all()
                        df = pd.DataFrame(docs)
                    else:
                        method = query_obj.get("method", "")
                        flt    = query_obj.get("filter", {})
                        cond   = tinydb_filter(flt)
                        
                        # Snapshot: docs to be affected
                        target_docs = table.search(cond) if cond else table.all()
                        snapshot = []
                        for d in target_docs:
                            sd = dict(d)
                            sd["__doc_id__"] = d.doc_id
                            snapshot.append(sd)

                        if method == "insert":
                            table.insert(query_obj.get("document", {}))
                            msg = "Inserted 1 record."
                            snapshot = None # No undo for inserts in this simple version
                        elif method == "update":
                            upd = query_obj.get("update", {})
                            for doc in target_docs:
                                new_doc = apply_smart_update(dict(doc), upd)
                                table.update(new_doc, doc_ids=[doc.doc_id])
                            msg = f"Updated {len(target_docs)} records."
                        elif method == "delete":
                            table.remove(cond)
                            msg = "Deleted matching records."
                        st.success(f"NoSQL Mutation ({method}) executed: {msg}")
                        df = pd.DataFrame()

                # Display Results...
                if not df.empty:
                    st.subheader("📊 Results")
                    st.dataframe(df)

                    # Visualization
                    st.subheader("📈 Visualization")
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    if len(numeric_cols) > 0 and len(categorical_cols) > 0:
                        fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0])
                        st.plotly_chart(fig)
                    
                    # AI Insights
                    st.subheader("🤖 AI Insights")
                    with st.spinner("Analyzing..."):
                        insights = generate_data_story(df, user_query)
                        st.markdown(insights)
                
                log_action(user_role, mode, user_query, "Success", db_type, snapshot)

            except Exception as e:
                st.error(f"Execution failed: {e}")
                log_action(user_role, mode, user_query, f"Failed: {e}")

        # Clear user_query in session state to prevent loop
        st.session_state.user_query = ""

with tab2:
    st.header("🩺 Data Health Check")
    if st.button("Run Health Scan"):
        with st.spinner("Scanning collection..."):
             total_docs_count = collection.count_documents({})
             sample_docs = list(collection.find().limit(100))
             
             issues = []
             null_counts = {}
             
             for doc in sample_docs:
                 for key, val in doc.items():
                     if val is None:
                         null_counts[key] = null_counts.get(key, 0) + 1
             
             if total_docs_count == 0:
                 score = 0
                 st.error("Collection is empty!")
             else:
                 score = 100
                 if null_counts:
                     score -= 20
                     issues.append(f"Found NULL values in fields: {list(null_counts.keys())}")
                 
                 st.metric("Health Score", f"{score}/100")
                 st.write(f"Scanned {len(sample_docs)} sample documents from {total_docs_count} total.")
                 
                 if issues:
                     for i in issues:
                         st.error(i)
                 else:
                     st.success("✅ Data looks clean! No obvious schema violations found in sample.")

with tab3:
    st.header("📝 Audit Log & Data Recovery")
    
    if not st.session_state.audit_log:
        st.info("No logs captured yet.")
    else:
        # Custom render to include buttons
        for i, entry in enumerate(reversed(st.session_state.audit_log)):
            idx = len(st.session_state.audit_log) - 1 - i
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 5, 1])
                with col1:
                    st.caption(entry["timestamp"])
                    st.write(f"**{entry['user']}**")
                    st.code(entry["db_type"] or "System", language="text")
                with col2:
                    st.write(f"**{entry['action']}**")
                    st.text(f"Query: {entry['query'][:100]}...")
                    status_color = "green" if "Success" in entry["status"] else "red"
                    st.markdown(f"Status: :{status_color}[{entry['status']}]")
                with col3:
                    if entry.get("snapshot") and not entry.get("undone"):
                        if st.button("Undo", key=f"undo_{idx}"):
                            if undo_mutation(idx):
                                st.success("Reverted!")
                                st.rerun()
                    elif entry.get("undone"):
                        st.info("Undone")
