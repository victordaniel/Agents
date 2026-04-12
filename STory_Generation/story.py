# GRADED FUNCTION: generate_draft

def generate_draft(topic: str, model: str = "openai:gpt-4o") -> str: 
    
    ### START CODE HERE ###

    # Define your prompt here. A multi-line f-string is typically used for this.
    prompt = f""" you are an essay writing expert. write an essay on the given topic:{topic} """

    ### END CODE HERE ###
    
    # Get a response from the LLM by creating a chat with the client.
    response = CLIENT.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )

    return response.choices[0].message.content

generate_draft("David and Goliath")