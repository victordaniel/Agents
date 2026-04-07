import json
import sqlite3
import os
import re
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env
load_dotenv()

# Setup Gemini API
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    client = genai.Client(api_key=API_KEY)
    model_id = 'gemini-3.1-flash-lite-preview'
else:
    client = None
    model_id = None

# -----------------------------
# 1. Generate SQL from question
# -----------------------------
def generate_sql(question: str, schema: str):
    prompt = f"""
You are a SQL assistant.
Given the schema and user question, write a SQLite query.

Schema:
{schema}

Question:
{question}

Return ONLY the SQL query. Do NOT use markdown code blocks (```sql). Just the raw SQL.
"""
    if not client:
        return "ERROR: Missing GEMINI_API_KEY"

    try:
        response = client.models.generate_content(model=model_id, contents=prompt)
        # Handle cases where response might be empty or blocked
        if not response.text:
            return "ERROR: Model returned empty response"
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


# -----------------------------
# 2. Run SQL on database
# -----------------------------
def run_sql(sql: str, db_path="example.db"):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        return result, None
    except Exception as e:
        return None, str(e)


# -----------------------------
# 3. Reflect using result + error
# -----------------------------
def reflect_sql(question: str, sql_query: str, schema: str, result, error):
    prompt = f"""
You are a SQL expert reviewing a query.

User question:
{question}

SQL query:
{sql_query}

Schema:
{schema}

Execution result:
{result}

Error (if any):
{error}

Does this correctly answer the user's question?
- If wrong, fix the SQL
- If error exists, fix the SQL
- If correct, return same SQL

Return STRICT JSON ONLY:
{{
  "feedback": "short explanation",
  "refined_sql": "final SQL query"
}}
"""
    if not client:
        return "ERROR: Missing GEMINI_API_KEY", sql_query

    try:
        response = client.models.generate_content(model=model_id, contents=prompt)
        content = response.text.strip()

        # Robust JSON extraction
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)

        obj = json.loads(content)
        feedback = obj.get("feedback", "")
        refined_sql = obj.get("refined_sql", sql_query)
    except Exception as e:
        feedback = f"Parsing Error: {str(e)}"
        refined_sql = sql_query

    return feedback, refined_sql


# -----------------------------
# 4. Full Agent Loop
# -----------------------------
def sql_agent(question, schema, db_path="example.db", max_iters=3):
    print("\n[Brain] Generating initial SQL...")
    sql = generate_sql(question, schema)
    print("Initial SQL:", sql)

    for i in range(max_iters):
        print(f"\n[Iter] Iteration {i+1}")
        result, error = run_sql(sql, db_path)

        print("Result:", result)
        print("Error:", error)

        feedback, new_sql = reflect_sql(question, sql, schema, result, error)

        print("Feedback:", feedback)
        print("Refined SQL:", new_sql)

        # Stop if no change or successful
        if new_sql.strip().lower() == sql.strip().lower():
            if result is not None:
                print("\n[Done] SQL converged.")
            else:
                print("\n[Error] SQL failed to correct itself.")
            break

        sql = new_sql

    return sql


# -----------------------------
# 5. Database Setup
# -----------------------------
def setup_db(db_path="example.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS customers;")
    cursor.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        revenue INTEGER
    );
    """)
    sample_data = [
        (1, "Alice", 50000), (2, "Bob", 75000), (3, "Charlie", 30000),
        (4, "Diana", 120000), (5, "Edward", 90000)
    ]
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?);", sample_data)
    conn.commit()
    conn.close()
    print(f"[Info] Database {db_path} ready.")


# -----------------------------
# 6. Main Execution
# -----------------------------
if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("[Error] GEMINI_API_KEY not found in environment or .env file.")
        print("Get a free key from https://aistudio.google.com/")
    else:
        setup_db("example.db")
        schema = "customers(id INTEGER, name TEXT, revenue INTEGER)"
        question = "Which customers have revenue greater than 80000?"

        final_sql = sql_agent(question, schema)
        print("\n" + "="*40)
        print("[Final Result] Best SQL Query found:")
        print(f"  {final_sql}")
        
        # Test it one last time
        res, err = run_sql(final_sql)
        print(f"\nFinal Result Set: {res}")
        if err: print(f"Final Error: {err}")
        print("="*40)
        print("\n[Result] Final SQL Result:", final_sql)