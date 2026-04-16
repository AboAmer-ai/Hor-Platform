import os
import requests
from .prompts import SYSTEM_PROMPT
from .memory import save_memory, get_memory
from .tools import get_jobs, search_jobs, add_job
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

def detect_tool(message: str):

    msg = message.lower()

    if "وظائف" in msg or "jobs" in msg:
        return "get_jobs"

    if "ابحث" in msg or "search" in msg:
        return "search_jobs"

    if "نشر وظيفة" in msg or "اضف وظيفة" in msg:
        return "add_job"

    return None

def run_agent(user_id, message):

    # =====================
    # TOOL DETECTION
    # =====================
    tool = detect_tool(message)

    if tool == "get_jobs":
        return get_jobs()

    if tool == "search_jobs":
        keyword = message.split()[-1]
        return search_jobs(keyword)

    if tool == "add_job":
        return "لإضافة وظيفة انتقل إلى صفحة نشر الوظائف وقم بملء البيانات."

    # =====================
    # AI CONVERSATION
    # =====================

    history = get_memory(user_id)

    conversation = SYSTEM_PROMPT + "\n\n"

    # آخر المحادثات فقط
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

    # حفظ المحادثة
    save_memory(user_id, f"User: {message}")
    save_memory(user_id, f"Assistant: {reply}")

    return reply
