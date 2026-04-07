import json
import sqlite3
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

client = OpenAI()

# -----------------------------
# 1. Generate SQL
# -----------------------------
def generate_sql(question, schema, model="gpt-4o"):
    prompt = f"""
You are a SQL assistant.

Schema:
{schema}

Question:
{question}

Return ONLY the SQL query.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


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
def reflect_without_result(question, sql_query, schema, model="gpt-4o"):
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
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        content = response.choices[0].message.content
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
def reflect_with_result(question, sql_query, schema, result, error, model="gpt-4o"):
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
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        content = response.choices[0].message.content
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
def evaluate(sql, db_path):
    result, error = run_sql(sql, db_path)
    if error:
        return "ERROR", error
    return "SUCCESS", result


# -----------------------------
# 6. MAIN EXPERIMENT
# -----------------------------
if __name__ == "__main__":
    schema = "customers(id, name, revenue)"
    db_path = "example.db"

    question = "Top 2 customers by revenue"

    # Step 1: generate initial SQL
    initial_sql = generate_sql(question, schema)
    print("\nInitial SQL:", initial_sql)

    # -----------------------------
    # Experiment 1
    # -----------------------------
    print("\n--- Experiment 1: WITHOUT result ---")
    sql1 = pipeline_without_result(question, initial_sql, schema)
    status1, output1 = evaluate(sql1, db_path)

    print("Final SQL:", sql1)
    print("Status:", status1)
    print("Output:", output1)

    # -----------------------------
    # Experiment 2
    # -----------------------------
    print("\n--- Experiment 2: WITH result ---")
    sql2 = pipeline_with_result(question, initial_sql, schema, db_path)
    status2, output2 = evaluate(sql2, db_path)

    print("Final SQL:", sql2)
    print("Status:", status2)
    print("Output:", output2)