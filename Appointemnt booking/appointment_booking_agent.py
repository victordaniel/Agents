# ==============================
# Appointment Agent using Gemini
# ==============================

import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# -----------------------------
# Setup
# -----------------------------
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.1-flash-lite-preview"

client = genai.Client(api_key=API_KEY)


# -----------------------------
# Database Setup
# -----------------------------
def setup_db():
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time TEXT
        )
        """)
        conn.commit()


# -----------------------------
# Tools (Functions)
# -----------------------------
def get_available_slots(date: str) -> dict:
    """Gets available appointment slots for a specific date.
    
    Args:
        date: The date to check (e.g., '2024-05-20')
    """
    all_slots = ["10:00", "11:00", "12:00", "14:00", "15:00"]
    
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT time FROM appointments WHERE date=?", (date,))
        booked = [row[0] for row in cursor.fetchall()]
    
    available = [slot for slot in all_slots if slot not in booked]
    return {"available_slots": available}


def check_availability(date: str, time: str) -> dict:
    """Checks if a specific time slot is available on a given date.
    
    Args:
        date: The date to check.
        time: The time to check.
    """
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM appointments WHERE date=? AND time=?",
            (date, time)
        )
        result = cursor.fetchone()
    
    return {"available": result is None}


def book_appointment(name: str, date: str, time: str) -> dict:
    """Books an appointment for a person at a specific date and time.
    
    Args:
        name: Name of the person booking.
        date: Date of the appointment.
        time: Time of the appointment.
    """
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (name, date, time) VALUES (?, ?, ?)",
            (name, date, time)
        )
        conn.commit()
    
    return {"status": "confirmed", "name": name, "date": date, "time": time}


# -----------------------------
# Agent Logic
# -----------------------------
def run_agent(user_input):
    """Runs the booking agent using native function calling."""
    
    # Define the system instruction
    system_instruction = """
    You are a professional appointment booking assistant. 
    
    Your goal is to help users find and book appointment slots.
    
    Follow these steps:
    1. If the user wants to book, first check available slots for that date using get_available_slots.
    2. If they specify a time, check if it's available using check_availability.
    3. Before calling book_appointment, ensure you have:
       - The user's name
       - The date
       - The time
    4. If info is missing, ask for it politely.
    5. Summarize the booking details once confirmed.
    
    Today is: """ + datetime.now().strftime("%Y-%m-%d")

    try:
        # Generate content with tools enabled
        # This uses automatic function calling if enabled in the SDK version
        # Otherwise, we handle it in a loop
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[get_available_slots, check_availability, book_appointment],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=False
            )
        )
        
        response = client.models.generate_content(
            model=MODEL,
            contents=user_input,
            config=config
        )
        
        return response.text

    except Exception as e:
        if "API key expired" in str(e):
            return "ERROR: Your Gemini API key has expired. Please renew it in your .env file."
        return f"ERROR: {str(e)}"


# -----------------------------
# CLI Demo
# -----------------------------
if __name__ == "__main__":
    setup_db()

    print("-" * 40)
    print("Appointment Booking Agent Initialized")
    print("Type 'exit' to quit")
    print("-" * 40)

    while True:
        try:
            user_text = input("\nYou: ")
            if user_text.lower() == "exit":
                break
            
            print("Thinking...")
            response = run_agent(user_text)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")