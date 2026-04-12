"""
Objective: Implement a function called revise_draft that improves a given essay draft based on feedback from a reflection step.

Inputs:

original_draft (str): The initial version of the essay.
reflection (str): Constructive feedback or critique on the draft.
model (str, optional): The model identifier to use. Defaults to "openai:gpt-4o".
Output:

A string containing the revised and improved essay.
Requirements:

The revised draft should address the issues mentioned in the feedback.
It should improve clarity, coherence, argument strength, and overall flow.
The function should use the feedback to guide the revision, and return only the final revised essay.
In this final exercise, you'll also need to manage the call to the LLM using the CLIENT, as you've practiced in previous exercises.
"""