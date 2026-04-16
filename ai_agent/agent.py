import os
import requests
from .prompts import SYSTEM_PROMPT
from .memory import save_memory, get_memory
from .tools import get_jobs, add_job, search_jobs

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}


def run_agent(user_id, message):

    history = get_memory(user_id)

    prompt = SYSTEM_PROMPT + "\n\n"

    for h in history[-6:]:
        prompt += f"{h}\n"

    prompt += f"\nUser: {message}\nAssistant:"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        output = response.json()

        if isinstance(output, list) and "generated_text" in output[0]:
            reply = output[0]["generated_text"]
        elif isinstance(output, dict) and "error" in output:
            print("HF ERROR:", output["error"])
            reply = "حدث خطأ في الذكاء الاصطناعي"
        else:
            reply = "لم يتم الحصول على رد من الذكاء الاصطناعي"

    except Exception as e:
        print("HF ERROR:", str(e))
        reply = "حدث خطأ في الذكاء الاصطناعي"

    save_memory(user_id, message)
    save_memory(user_id, reply)

    return reply
