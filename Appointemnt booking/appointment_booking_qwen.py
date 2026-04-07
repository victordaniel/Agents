# ==========================================
# Appointment Agent - ULTRA FAST (Local)
# Model: Qwen 2.5 0.5B (Local via Ollama)
# ==========================================

import os
import sqlite3
import json
from datetime import datetime
import ollama 

# -----------------------------
# Config (High Speed Selection)
# -----------------------------
MODEL = "qwen2.5:0.5b" 

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
            name TEXT, date TEXT, time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

# -----------------------------
# Tools (Optimized for JSON)
# -----------------------------
def get_available_slots(date: str) -> str:
    """Check slots for YYYY-MM-DD."""
    all_slots = ["10:00", "11:00", "12:00", "14:00", "15:00"]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT time FROM appointments WHERE date=?", (date,))
        booked = [row[0] for row in cursor.fetchall()]
    available = [slot for slot in all_slots if slot not in booked]
    return json.dumps({"available": available})

def book_appointment(name: str, date: str, time: str) -> str:
    """Book a slot for Name, Date, Time."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO appointments (name, date, time) VALUES (?, ?, ?)", (name, date, time))
        conn.commit()
    return json.dumps({"status": "SUCCESS"})

def get_all_bookings() -> str:
    """List all current bookings."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, date, time FROM appointments")
        rows = cursor.fetchall()
    return json.dumps([{"name": r[0], "date": r[1], "time": r[2]} for r in rows])

# Tool Routing Map
TOOLS_MAP = {
    'get_available_slots': get_available_slots,
    'book_appointment': book_appointment,
    'get_all_bookings': get_all_bookings,
}

# -----------------------------
# High-Speed ReAct Loop
# -----------------------------
class FastAgent:
    def __init__(self):
        self.messages = [{
            'role': 'system', 
            'content': f'You are a professional appointment assistant. Today is {datetime.now().strftime("%Y-%m-%d")}. '
                       f'Always use tools to check availability or book appointments. '
                       f'After using a tool, summarize the result for the user in a natural way.'
        }]

    def ask(self, user_input):
        self.messages.append({'role': 'user', 'content': user_input})
        
        response = ollama.chat(
            model=MODEL,
            messages=self.messages,
            tools=[get_available_slots, book_appointment, get_all_bookings],
        )

        while response.get('message', {}).get('tool_calls'):
            self.messages.append(response['message'])
            for tool in response['message']['tool_calls']:
                func = tool['function']['name']
                args = tool['function']['arguments']
                # If args is a string, parse it
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        pass
                
                # Normalizing args to lowercase
                args = {k.lower(): v for k, v in args.items()}
                print(f"[Ollama] Calling: {func}")
                result = TOOLS_MAP[func](**args)
                
                # Add tool response including ID if present
                tool_msg = {'role': 'tool', 'content': result}
                if 'id' in tool:
                    tool_msg['id'] = tool['id']
                self.messages.append(tool_msg)

            response = ollama.chat(
                model=MODEL, 
                messages=self.messages,
                tools=[get_available_slots, book_appointment, get_all_bookings]
            )

        final_msg = response['message'].get('content', '')
        if not final_msg:
             final_msg = "The operation was completed successfully."
        self.messages.append({'role': 'assistant', 'content': final_msg})
        return final_msg

# -----------------------------
# Launch
# -----------------------------
if __name__ == "__main__":
    setup_db()
    agent = FastAgent()
    print(">>> LOCAL ULTRA-FAST AGENT READY (Qwen 0.5B)")

    while True:
        txt = input("\nYou: ")
        if txt.lower() in ['exit', 'quit']: break
        print(f"Agent: {agent.ask(txt)}")
