import ollama

def test_tool(name: str):
    return f"Hello {name}"

response = ollama.chat(
    model="qwen2.5:0.5b",
    messages=[{"role": "user", "content": "Tell John hello"}],
    tools=[test_tool]
)

print(f"Message: {response['message']}")
