import random
import requests
import json
import os

# ========================================================================
# 📖 CONFIGURATION
# ========================================================================

# The endpoint where Ollama runs locally
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma:2b" 

# --- The Knowledge Base ---
# For simplicity, we store a list of sample verses here. 
# In a real production system, this list might be loaded from a large CSV or JSON file.
SAMPLE_BIBLE_VERSES = [
    "John 3:16 - For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
    "Psalm 23:1 - The Lord is my shepherd; I shall not want. He maketh me to lie down in green pastures: he leadeth me beside the still waters.",
    "Philippians 4:13 - I can do all things through Christ which strengtheneth me.",
    "Romans 8:28 - And we know that all things work together for good to them that love God, that they are called according to his purpose.",
    "Matthew 6:33 - But seek ye first the kingdom of God, and his righteousness; and all these things shall be added unto you.",
]


# ========================================================================
# ⚙️ FUNCTION DEFINITIONS
# ========================================================================

def get_random_verse(verses: list) -> str:
    """
    Selects one verse randomly from the pre-loaded list.
    """
    selected_verse = random.choice(verses)
    print("\n" + "="*60)
    print("🕊️ Random Scripture Selection Complete! 🕊️")
    print("="*60)
    return selected_verse

def generate_reflection_with_llm(verse: str) -> str:
    """
    Sends the selected verse to the local Gemma 4 model via Ollama API 
    to get a polished reflection.
    """
    print(f"\n[🤖 Thinking... Sending verse to {MODEL_NAME} for reflection...]")
    
    # 1. Define the System Role (The Prompt Engineering)
    # This tells the LLM *who* it is and *how* to format the output.
    system_prompt = (
        "You are a revered, poetic, and encouraging biblical interpreter. "
        "Your task is to take a single Bible verse and expand on its meaning. "
        "The output MUST be formatted perfectly: Start with the verse in a quote block, "
        "followed by a brief, two-paragraph reflection that speaks to modern life, "
        "and conclude with a final blessing. DO NOT include any introduction or conversational text."
    )
    
    # 2. Construct the final user prompt
    full_prompt = f"Here is the verse to reflect on: \"{verse}\""

    # 3. Ollama API Payload
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "system": system_prompt,  # Using the system role for better control
        "options": {
            "temperature": 0.7, # Controls creativity (0.0 is least creative)
        }
    }

    try:
        # Send the request to the local Ollama API
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status() # Check for HTTP errors (4xx, 5xx)
        
        # Parse the response and extract the generated text
        data = response.json()
        return data.get("response", "Error: Could not retrieve a response from the model.")

    except requests.exceptions.ConnectionError:
        return (
            "❌ ERROR: Could not connect to Ollama. "
            "Please ensure the Ollama server is running in the background, "
            "and that you have pulled the model ("
            f"ollama pull {MODEL_NAME})."
        )
    except requests.exceptions.RequestException as e:
        return f"❌ An error occurred during the API call: {e}"


def run_agent():
    """
    The main function to run the entire Bible Agent workflow.
    """
    print("="*70)
    print(f"✨ Starting the Gemma 4 Scripture Agent using {MODEL_NAME} ✨")
    print("="*70)

    # Step 1: Randomly select the verse
    random_verse = get_random_verse(SAMPLE_BIBLE_VERSES)
    
    # Step 2: Pass the verse to the LLM for reflection
    reflection = generate_reflection_with_llm(random_verse)
    
    # Step 3: Display the final output
    print("\n\n" + "="*60)
    print("✨ GENERATION COMPLETE ✨")
    print("="*60)
    
    print("\n📜 BIBLE VERSE 📜")
    print(f"-> {random_verse}")
    print("\n" + "~"*60)
    print("\n✨ REFLECTION FROM THE AGENT ✨")
    print(reflection)
    print("\n" + "="*70)


# ========================================================================
# 🚀 EXECUTION
# ========================================================================
if __name__ == "__main__":
    run_agent()
