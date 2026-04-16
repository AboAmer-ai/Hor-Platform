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

    # إضافة الذاكرة
    if history:
    prompt += "سجل المحادثة:\n"
    for h in history[-6:]:
        prompt += f"- {h}\n"

    # الرسالة الحالية (مع السياق)
    prompt += f"\nUser: {message}\nAssistant:"

    payload = {
    "inputs": prompt,
    "parameters": {
        "max_new_tokens": 180,
        "temperature": 0.8,
        "repetition_penalty": 1.2
    }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        output = response.json()

        # إصلاح قراءة HuggingFace (مهم جداً)
        if isinstance(output, list) and "generated_text" in output[0]:
            full_text = output[0]["generated_text"]
            reply = full_text.split("Assistant:")[-1].strip()
        else:
            reply = fallback_reply(message)

    except:
        reply = fallback_reply(message)

    save_memory(user_id, message)
    save_memory(user_id, reply)

    return reply
