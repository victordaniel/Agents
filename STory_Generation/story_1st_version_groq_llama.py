from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def generate_draft(topic: str, model: str = "llama-3.1-8b-instant") -> str:
    
    prompt = f"""
You are a story writing expert.
Write a story on the topic: {topic}.
Include introduction, body, and conclusion.
"""

    response = CLIENT.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content


print(generate_draft("David and Goliath"))



