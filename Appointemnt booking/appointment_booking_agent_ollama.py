# ==========================================
# Appointment Agent v3.0 (LOCAL - Gemma 4)
# ==========================================

import os
import sqlite3
import json
from datetime import datetime, timedelta
import ollama  # Local inference library

# -----------------------------
# Config
# -----------------------------
MODEL = "gemma4" # Ensure this matches your 'ollama list' output

# -----------------------------
# Database Management
# -----------------------------
def get_db_connection():
    return sqlite3.connect("appointments.db")

def setup_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

# -----------------------------
# Tools (Python Side)
# -----------------------------
def get_available_slots(date: str) -> str:
    """Gets available appointment slots for a specific date (YYYY-MM-DD)."""
    all_slots = ["10:00", "11:00", "12:00", "14:00", "15:00"]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT time FROM appointments WHERE date=?", (date,))
        booked = [row[0] for row in cursor.fetchall()]
    available = [slot for slot in all_slots if slot not in booked]
    return json.dumps({"date": date, "available": available})

def check_availability(date: str, time: str) -> str:
    """Checks if a specific time slot is free."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE date=? AND time=?", (date, time))
        result = cursor.fetchone()
    return json.dumps({"available": result is None})

def book_appointment(name: str, date: str, time: str) -> str:
    """Books an appointment. Requires Name, Date, and Time."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO appointments (name, date, time) VALUES (?, ?, ?)", (name, date, time))
        conn.commit()
    return json.dumps({"status": "SUCCESS", "booking": {"name": name, "date": date, "time": time}})

def get_all_bookings() -> str:
    """Lists every booking currently in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, date, time FROM appointments ORDER BY date ASC")
        rows = cursor.fetchall()
    return json.dumps([{"name": r[0], "date": r[1], "time": r[2]} for r in rows])

# Map tools for the internal loop
TOOLS_MAP = {
    'get_available_slots': get_available_slots,
    'check_availability': check_availability,
    'book_appointment': book_appointment,
    'get_all_bookings': get_all_bookings,
}

# -----------------------------
# Agent Loop
# -----------------------------
class LocalAgent:
    def __init__(self):
        self.messages = [
            {'role': 'system', 'content': f'Today is {datetime.now().strftime("%Y-%m-%d")}. You are a booking assistant. Use the tools provided to manage appointments.'}
        ]

    def ask(self, user_input):
        self.messages.append({'role': 'user', 'content': user_input})
        
        # Initial call to model
        response = ollama.chat(
            model=MODEL,
            messages=self.messages,
            tools=[get_available_slots, check_availability, book_appointment, get_all_bookings],
        )

        # Handle tool calls (the ReAct loop)
        while response.get('message', {}).get('tool_calls'):
            self.messages.append(response['message'])
            
            for tool in response['message']['tool_calls']:
                func_name = tool['function']['name']
                args = tool['function']['arguments']
                
                print(f"⚙️ Local Tool Call: {func_name}({args})")
                
                result = TOOLS_MAP[func_name](**args)
                
                self.messages.append({
                    'role': 'tool',
                    'content': result,
                })
            
            # Get updated response from model after tool execution
            response = ollama.chat(model=MODEL, messages=self.messages)

        final_content = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': final_content})
        return final_content

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    setup_db()
    agent = LocalAgent()

    print("-" * 40)
    print("LOCAL APPOINTMENT AGENT (Gemma 4 via Ollama)")
    print("-" * 40)

    while True:
        user_text = input("\nYou: ")
        if user_text.lower() in ['exit', 'quit']: break
        
        print("Model is thinking locally...")
        print(f"\nAgent: {agent.ask(user_text)}")
