from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def generate_stream(topic):
    prompt = f"""
You are a story writing expert.
Write a story on the topic: {topic}.
Include introduction, body, and conclusion.
"""

    response = CLIENT.chat.completions.create(
        model="llama-3.1-8b-instant",   
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in response:
        print(chunk.choices[0].delta.content or "", end="", flush=True)


generate_stream("David and Goliath")