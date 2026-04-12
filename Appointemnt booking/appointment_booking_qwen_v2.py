# ==========================================
# FINAL APPOINTMENT AGENT (PRO VERSION)
# Local LLM + ReAct + Robust Logic
# ==========================================

import sqlite3
import json
from datetime import datetime, timedelta
import ollama

MODEL = "qwen2.5:0.5b"  # Fall back to 0.5b for faster testing until 3b or 7b are fully loaded

# -----------------------------
# DATABASE
# -----------------------------
def get_db():
    return sqlite3.connect("appointments.db")

def setup_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

# -----------------------------
# DATE NORMALIZATION
# -----------------------------
def normalize_date(text):
    text = text.lower()
    today = datetime.now()

    if "today" in text:
        return today.strftime("%Y-%m-%d")

    if "tomorrow" in text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    return text  # fallback

# -----------------------------
# TOOLS
# -----------------------------
def get_available_slots(date: str):
    all_slots = ["10:00", "11:00", "12:00", "14:00", "15:00"]

    with get_db() as conn:
        rows = conn.execute(
            "SELECT time FROM appointments WHERE date=?", (date,)
        ).fetchall()

    booked = [r[0] for r in rows]
    available = [s for s in all_slots if s not in booked]

    return {"status": "success", "available_slots": available}


def safe_book(name: str, date: str, time: str):
    slots = get_available_slots(date)["available_slots"]

    if time not in slots:
        return {"status": "error", "message": "Slot not available"}

    with get_db() as conn:
        conn.execute(
            "INSERT INTO appointments (name, date, time) VALUES (?, ?, ?)",
            (name, date, time)
        )

    return {"status": "confirmed", "name": name, "date": date, "time": time}


def get_all_bookings():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT name, date, time FROM appointments"
        ).fetchall()

    return [{"name": r[0], "date": r[1], "time": r[2]} for r in rows]


TOOLS = {
    "get_available_slots": get_available_slots,
    "safe_book": safe_book,
    "get_all_bookings": get_all_bookings,
}

# -----------------------------
# ARG VALIDATION
# -----------------------------
def validate_args(func, args):
    required = func.__code__.co_varnames[:func.__code__.co_argcount]
    missing = [r for r in required if r not in args]

    if missing:
        return False, f"Missing args: {missing}"

    return True, None

# -----------------------------
# AGENT
# -----------------------------
class Agent:
    def __init__(self):
        self.messages = []
        self.session = {"name": None, "date": None, "time": None}

        self.system = {
            "role": "system",
            "content": f"You are a professional appointment assistant. Today is {datetime.now().strftime('%Y-%m-%d')}. "
                       f"Always use tools to check availability or book appointments. "
                       f"After using a tool, summarize the result for the user in a natural way."
        }

        self.messages.append(self.system)

    # -------------------------
    def extract_entities(self, text):
        """Simple slot extraction"""
        text = text.lower()

        if "tomorrow" in text:
            self.session["date"] = normalize_date(text)

        if any(t in text for t in ["10", "11", "12", "14", "15"]):
            for t in ["10:00", "11:00", "12:00", "14:00", "15:00"]:
                if t[:2] in text:
                    self.session["time"] = t

        # crude name detection
        if len(text.split()) == 1:
            self.session["name"] = text.title()

    # -------------------------
    def ask(self, user_input):
        self.extract_entities(user_input)

        self.messages.append({"role": "user", "content": user_input})

        print(f"[Debug] Querying {MODEL} with tools...")
        response = ollama.chat(
            model=MODEL,
            messages=self.messages,
            tools=[get_available_slots, safe_book, get_all_bookings],
        )

        # -------- DEBUG --------
        print(f"[Debug] Model response: {response['message']}")

        # -------- REACT LOOP --------
        while response.get("message", {}).get("tool_calls"):
            self.messages.append(response["message"])

            for tool in response["message"]["tool_calls"]:
                name = tool["function"]["name"]
                args = tool["function"]["arguments"]

                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        args = {}

                args = {k.lower(): v for k, v in args.items()}

                print(f"[Tool Call] {name} -> {args}")

                if name in TOOLS:
                    valid, err = validate_args(TOOLS[name], args)

                    if not valid:
                        result = {"error": err}
                    else:
                        result = TOOLS[name](**args)
                else:
                    result = {"error": "Tool not found"}

                # CRITICAL: Always include the tool_call_id
                tool_msg = {
                    "role": "tool",
                    "content": json.dumps(result)
                }
                if "id" in tool:
                    tool_msg["id"] = tool["id"]
                self.messages.append(tool_msg)

            response = ollama.chat(
                model=MODEL,
                messages=self.messages,
                tools=[get_available_slots, safe_book, get_all_bookings]
            )

        final = response["message"].get("content", "")

        if not final:
            final = "Done."

        self.messages.append({"role": "assistant", "content": final})
        return final


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    setup_db()
    agent = Agent()

    print("\nFINAL APPOINTMENT AGENT READY\n")

    while True:
        try:
            txt = input("You: ")

            if txt.lower() in ["exit", "quit"]:
                break

            reply = agent.ask(txt)
            print("Agent:", reply)

        except KeyboardInterrupt:
            break