import os
from openai import OpenAI
from .prompts import SYSTEM_PROMPT
from .memory import save_memory, get_memory
from .tools import get_jobs, add_job, search_jobs
# إنشاء العميل
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)


def run_agent(user_id, message):

    history = get_memory(user_id)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # إضافة الذاكرة السابقة
    for h in history:
        messages.append({
            "role": "user",
            "content": h
        })

    # رسالة المستخدم الحالية
    messages.append({
        "role": "user",
        "content": message
    })

    # استدعاء الذكاء الاصطناعي
    response = client.responses.create(
        model="gpt-5.2",
        input=messages
    )

    reply = response.output_text

    # حفظ الذاكرة
    save_memory(user_id, message)
    save_memory(user_id, reply)

    return reply
