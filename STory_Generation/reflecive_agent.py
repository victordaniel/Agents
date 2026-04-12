"""
Exercise : reflect_on_draft Function
Objective: Write a function called reflect_on_draft that takes a previously generated essay draft and uses a language model to provide constructive feedback.

Inputs:

draft (str): The essay text to reflect on.
model (str, optional): The model identifier to use. Defaults to "openai:o4-mini".
Output:

A string with feedback in paragraph form.
Requirements:

The feedback should be critical but constructive.
It should address issues such as structure, clarity, strength of argument, and writing style.
The function should send the draft to the model and return its response.
You do not need to rewrite the essay at this step—just analyze and reflect on it.



"""



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
Include introduction, body, and conclusion and 
also bible reference and life application
"""

    response = CLIENT.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
 
    return response.choices[0].message.content


#rint(generate_draft("David and Goliath"))

#****************************************************



def reflect_on_draft(draft: str, model: str = "llama-3.1-8b-instant") -> str:
    
    prompt = f"""
You are an expert writing critic.

Analyze the following essay and provide constructive feedback.

Focus on:
- Structure (organization, flow)
- Clarity (readability, coherence)
- Strength of argument
- Writing style (tone, grammar, engagement)
-check if the essay includes bible reference and life application
-check the life application is relevant to the story and has practical application
-check if the essay has a clear introduction, body, and conclusion
-check if the essay has a clear and relevant bible reference
-check if the essay has a clear and relevant life application
-check if the essay has a clear and relevant life application that is practical and can be applied to daily life
-check if this is most interesting to the youtube audience
Be critical but constructive. Write in paragraph form.

Essay:
{draft}
"""

    response = CLIENT.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,  # lower for analytical tasks
    )

    return response.choices[0].message.content

# Example usage
draft = generate_draft("David and Goliath")
feedback = reflect_on_draft(draft)


print("\n" + "="*50 + "=Draft" + "="*50 + "\n")
print(draft)
print("\n" + "="*50 + "=Feedback" + "="*50 + "\n")
print(feedback)





