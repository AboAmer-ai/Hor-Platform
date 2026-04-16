import os
import requests
from .prompts import SYSTEM_PROMPT
from .memory import save_memory, get_memory

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}


def fallback_reply(message: str) -> str:
    """ردود احتياطية ذكية بدون API"""

    msg = message.lower()

    if "مرحبا" in msg or "hello" in msg:
        return "أهلاً بك 👋 كيف أقدر أساعدك اليوم؟"

    if "وظيفة" in msg:
        return "تقدر تتصفح الوظائف أو تنشر وظيفة جديدة بسهولة من المنصة."

    if "مساعدة" in msg:
        return "أنا هنا لمساعدتك، اكتب سؤالك وسأرد عليك."

    return "أنا جاهز لمساعدتك، اكتب سؤالك بشكل أوضح 😊"


def run_agent(user_id, message):

    history = get_memory(user_id)

    prompt = SYSTEM_PROMPT + "\n\n"

    for h in history[-6:]:
        prompt += f"{h}\n"

    prompt += f"\nUser: {message}\nAssistant:"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)

        try:
            output = response.json()
        except:
            output = None

        if isinstance(output, list) and "generated_text" in output[0]:
            reply = output[0]["generated_text"]
        elif isinstance(output, dict) and "error" in output:
            reply = fallback_reply(message)
        else:
            reply = fallback_reply(message)

    except:
        reply = fallback_reply(message)

    save_memory(user_id, message)
    save_memory(user_id, reply)

    return reply
