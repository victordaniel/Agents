import requests

def generate_draft(title):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": f"Write a short Bible story about {title} in telugu",
            "stream": False
        }
    )

    return response.json()["response"]

print(generate_draft("David and Goliath"))