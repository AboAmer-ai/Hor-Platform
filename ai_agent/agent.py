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

    conversation = SYSTEM_PROMPT + "\n\n"

    # اخر محادثات فقط
    for h in history[-6:]:
        conversation += h + "\n"

    conversation += f"User: {message}\nAssistant:"

    payload = {
        "inputs": conversation,
        "parameters": {
            "max_new_tokens": 180,
            "temperature": 0.9,
            "top_p": 0.95,
            "repetition_penalty": 1.3,
            "do_sample": True
        }
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=20
        )

        output = response.json()

        if isinstance(output, list):
            text = output[0]["generated_text"]
            reply = text.split("Assistant:")[-1].strip()
        else:
            reply = fallback_reply(message)

    except:
        reply = fallback_reply(message)

    # حفظ المحادثة بشكل صحيح
    save_memory(user_id, f"User: {message}")
    save_memory(user_id, f"Assistant: {reply}")

    return reply
