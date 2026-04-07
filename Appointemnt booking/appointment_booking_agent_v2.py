# ==========================================
# Appointment Agent v2.0 (Production-Ready)
# ==========================================

import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
from google.genai import types

# -----------------------------
# Setup & Config
# -----------------------------
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash" 

client = genai.Client(api_key=API_KEY)

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
# Date Normalization Logic
# -----------------------------
def normalize_date(date_str: str) -> str:
    """Helper to convert relative dates (tomorrow) to YYYY-MM-DD."""
    today = datetime.now()
    date_str = date_str.lower().strip()
    
    if "today" in date_str:
        return today.strftime("%Y-%m-%d")
    elif "tomorrow" in date_str:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Basic attempt to parse or return original
    # In production, use 'dateparser' library for 100% robustness
    return date_str

# -----------------------------
# Agent Tools (The "Brawn")
# -----------------------------
def get_available_slots(date: str) -> dict:
    """Gets available appointment slots for a specific date (e.g. '2024-05-20')."""
    date = normalize_date(date)
    all_slots = ["10:00", "11:00", "12:00", "14:00", "15:00"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT time FROM appointments WHERE date=?", (date,))
        booked = [row[0] for row in cursor.fetchall()]
    
    available = [slot for slot in all_slots if slot not in booked]
    return {"date_checked": date, "available_slots": available}

def check_availability(date: str, time: str) -> dict:
    """Strict check: returns True if a specific time slot is free."""
    date = normalize_date(date)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE date=? AND time=?", (date, time))
        result = cursor.fetchone()
    
    return {"date": date, "time": time, "is_available": result is None}

def book_appointment(name: str, date: str, time: str) -> dict:
    """Commits a booking to the database. Requires Name, Date, and Time."""
    date = normalize_date(date)
    
    # Final safety check before insert
    if not check_availability(date, time)["is_available"]:
        return {"error": "Slot already taken. Choose another time."}

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (name, date, time) VALUES (?, ?, ?)",
            (name, date, time)
        )
        conn.commit()
    
    return {"status": "SUCCESS", "details": {"name": name, "date": date, "time": time}}

def get_all_bookings() -> dict:
    """Admin tool: Lists every booking currently in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, date, time FROM appointments ORDER BY date ASC")
        rows = cursor.fetchall()
    
    bookings = [{"name": r[0], "date": r[1], "time": r[2]} for r in rows]
    return {"total_count": len(bookings), "bookings": bookings}

# -----------------------------
# Orchestration Logic (The "Brain")
# -----------------------------
class AppointmentAgent:
    def __init__(self):
        self.system_instruction = f"""
        You are an elite Appointment Booking Agent. 
        Current System Date: {datetime.now().strftime("%Y-%m-%d")}

        CORE PROTOCOLS:
        1. PERSISTENCE: You remember names and dates. If the user said "My name is Victor" 
           5 minutes ago, do not ask for it again.
        2. SLOT FILLING: To book an appointment, you MUST have: [NAME, DATE, TIME].
        3. GROUNDING: Never say an appointment is booked unless the 'book_appointment' 
           tool returns "SUCCESS". 
        4. RELATIVE DATES: If the user says "tomorrow" or "next Monday", 
           just pass that string to the tools—they handle normalization.
        5. ADMIN: If asked to "show all bookings", use the get_all_bookings tool.

        BEHAVIOR:
        - Be professional and concise.
        - If a slot is taken, suggest the NEXT available slot immediately.
        - Do not greet repeatedly in the same conversation.
        """
        
        # Initialize the stateful chat session
        self.chat = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                tools=[get_available_slots, check_availability, book_appointment, get_all_bookings],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

    def ask(self, user_text):
        try:
            response = self.chat.send_message(user_text)
            return response.text
        except Exception as e:
            if "API key expired" in str(e):
                return "CRITICAL ERROR: Please update your API Key in .env"
            return f"Error: {str(e)}"

# -----------------------------
# Interface
# -----------------------------
if __name__ == "__main__":
    setup_db()
    agent = AppointmentAgent()

    print("="*50)
    print("APPOINTMENT AGENT v2.0 ONLINE")
    print("="*50)

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            print("Thinking...")
            reply = agent.ask(user_input)
            print(f"\nAgent: {reply}")
            
        except KeyboardInterrupt:
            break
