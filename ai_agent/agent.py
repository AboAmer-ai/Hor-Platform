
import os
from openai import OpenAI
from .prompts import SYSTEM_PROMPT
from .memory import save_memory, get_memory

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_agent(user_id, message):

    history = get_memory(user_id)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    for h in history:
        messages.append({"role": "user", "content": h})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=messages,
    )

    reply = response.choices[0].message.content

    save_memory(user_id, message)
    save_memory(user_id, reply)

    return reply
