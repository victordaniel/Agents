import json
import sqlite3
import os
import re
from dotenv import load_dotenv
from google import genai

# -----------------------------
# Setup
# -----------------------------
load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=API_KEY)

MODEL_ID = "gemini-3.1-flash-lite-preview"


# -----------------------------
# Helper: Call Gemini
# -----------------------------
def call_gemini(prompt):
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
        )
        if not response.text:
            return "ERROR: Empty response from model"
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


# -----------------------------
# 1. Generate SQL
# -----------------------------
def generate_sql(question, schema):
    prompt = f"""
You are a SQL assistant.

Schema:
{schema}

Question:
{question}

Return ONLY the SQL query.
"""
    return call_gemini(prompt)


# -----------------------------
# 2. Run SQL
# -----------------------------
def run_sql(sql, db_path="example.db"):
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
# 3A. Reflection WITHOUT result
# -----------------------------
def reflect_without_result(question, sql_query, schema):
    prompt = f"""
User question:
{question}

SQL query:
{sql_query}

Schema:
{schema}

Does this SQL correctly answer the question?
If not, fix it.

Return STRICT JSON:
{{
  "feedback": "short explanation",
  "refined_sql": "final SQL"
}}
"""
    content = call_gemini(prompt)

    try:
        # Robust JSON extraction
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
            
        obj = json.loads(content)
        return obj.get("feedback", ""), obj.get("refined_sql", sql_query)
    except Exception as e:
        return f"Parsing Error: {str(e)}", sql_query


# -----------------------------
# 3B. Reflection WITH result
# -----------------------------
def reflect_with_result(question, sql_query, schema, result, error):
    prompt = f"""
User question:
{question}

SQL query:
{sql_query}

Schema:
{schema}

Execution result:
{result}

Error:
{error}

Does this result correctly answer the question?

- If wrong, fix SQL
- If error, fix SQL
- If correct, keep same SQL

Return STRICT JSON:
{{
  "feedback": "short explanation",
  "refined_sql": "final SQL"
}}
"""
    content = call_gemini(prompt)

    try:
        # Robust JSON extraction
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
            
        obj = json.loads(content)
        return obj.get("feedback", ""), obj.get("refined_sql", sql_query)
    except Exception as e:
        return f"Parsing Error: {str(e)}", sql_query


# -----------------------------
# 4A. Pipeline WITHOUT result
# -----------------------------
def pipeline_without_result(question, initial_sql, schema, max_iters=3):
    sql = initial_sql

    for _ in range(max_iters):
        feedback, new_sql = reflect_without_result(question, sql, schema)

        if new_sql.strip() == sql.strip():
            break

        sql = new_sql

    return sql


# -----------------------------
# 4B. Pipeline WITH result
# -----------------------------
def pipeline_with_result(question, initial_sql, schema, db_path, max_iters=3):
    sql = initial_sql

    for _ in range(max_iters):
        result, error = run_sql(sql, db_path)

        feedback, new_sql = reflect_with_result(
            question, sql, schema, result, error
        )

        if new_sql.strip() == sql.strip():
            break

        sql = new_sql

    return sql


# -----------------------------
# 5. Evaluation
# -----------------------------
def evaluate(sql, db_path="example.db"):
    result, error = run_sql(sql, db_path)

    if error:
        return {"status": "ERROR", "result": None, "error": error}

    return {"status": "SUCCESS", "result": result, "error": None}


# -----------------------------
# 6. Database Setup
# -----------------------------
def setup_db(db_path="example.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS customers;")

    cursor.execute("""
    CREATE TABLE customers (
        id INTEGER,
        name TEXT,
        revenue INTEGER
    );
    """)

    data = [
        (1, "Alice", 50000),
        (2, "Bob", 75000),
        (3, "Charlie", 30000),
        (4, "Diana", 120000),
        (5, "Edward", 90000)
    ]

    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?)", data)

    conn.commit()
    conn.close()


# -----------------------------
# 7. Compare Results
# -----------------------------
def compare(exp1, exp2):
    print("\n========== COMPARISON ==========")

    print("\nExperiment 1 (NO RESULT):")
    print(exp1)

    print("\nExperiment 2 (WITH RESULT):")
    print(exp2)

    if exp1["status"] == "SUCCESS" and exp2["status"] == "SUCCESS":
        print("\n[SUCCESS] Both succeeded")
    elif exp2["status"] == "SUCCESS":
        print("\n[WINNER] WITH RESULT is better")
    elif exp1["status"] == "SUCCESS":
        print("\n[WINNER] WITHOUT RESULT is better")
    else:
        print("\n[FAILED] Both failed")


# -----------------------------
# 8. MAIN
# -----------------------------
if __name__ == "__main__":
    setup_db()

    schema = "customers(id, name, revenue)"
    question = "Get top 2 customers by revenue"

    print("\n[Step 1] Generating initial SQL...")
    initial_sql = generate_sql(question, schema)
    print("Initial SQL:", initial_sql)

    print("\n--- Experiment 1: WITHOUT RESULT ---")
    sql1 = pipeline_without_result(question, initial_sql, schema)
    eval1 = evaluate(sql1)
    print("Final SQL:", sql1)
    print("Evaluation:", eval1)

    print("\n--- Experiment 2: WITH RESULT ---")
    sql2 = pipeline_with_result(question, initial_sql, schema, "example.db")
    eval2 = evaluate(sql2)
    print("Final SQL:", sql2)
    print("Evaluation:", eval2)

    compare(eval1, eval2)