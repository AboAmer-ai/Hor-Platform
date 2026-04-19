import os
import requests
import random

from .prompts import SYSTEM_PROMPT
from .memory import save_memory, get_memory
from .tools import get_jobs, search_jobs, add_job

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# =========================
# FAQ BRAIN
# =========================

def search_faq(message):

    try:
        with open("ai-agent/faq.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()

        msg = message.lower()

        for line in lines:
            if "|" not in line:
                continue

            q, a = line.strip().split("|", 1)

            if q.lower() in msg:
                return a

    except:
        pass

    return None


# =========================
# FALLBACK BRAIN
# =========================


def fallback_reply(message):

    replies = [

        # ترحيب ومساعدة عامة
        "أنا معك 👋 كيف أقدر أساعدك داخل منصة حُر؟",
        "يسعدني مساعدتك 😊 هل تبحث عن وظيفة أم تريد نشر وظيفة؟",
        "قلّي ماذا تريد أن تفعل وسأرشدك خطوة بخطوة.",
        "موجود لمساعدتك في استخدام المنصة بسهولة 👍",

        # توجيه ذكي
        "هل تريد تصفح الوظائف المتاحة أم معرفة طريقة التقديم؟",
        "يمكنني مساعدتك في إيجاد وظيفة مناسبة لك أو نشر وظيفة جديدة.",
        "اكتب لي ما الذي تبحث عنه وسأوجهك مباشرة.",
        "لو تبحث عن وظيفة، اكتب تخصصك وسأحاول مساعدتك.",

        # تحفيز المستخدم
        "ابدأ بسؤالي عن الوظائف أو طريقة التقديم وسأشرح لك فوراً 🚀",
        "يمكننا البدء بالبحث عن وظائف مناسبة لك الآن.",
        "ما المجال الذي تهتم بالعمل فيه؟",

        # دعم الاستخدام
        "إذا كنت جديداً هنا يمكنني شرح كيفية استخدام المنصة بسهولة.",
        "أنا مساعد منصة حُر، جاهز لإرشادك في أي خطوة تحتاجها.",
        "جرّب أن تسأل: كيف أقدم؟ أو اعرض الوظائف.",

        # ذكي وغير روبوتي
        "سؤالك جميل 👍 هل تستطيع توضيحه قليلاً لأساعدك بشكل أدق؟",
        "أحب أساعدك بأفضل طريقة، ماذا تريد أن تفعل تحديداً؟",
        "خلينا نبدأ 😊 هل هدفك البحث عن عمل أم إضافة وظيفة؟",

        # إعادة توجيه ناعمة
        "يمكنك سؤالي عن الوظائف، التقديم، أو نشر وظيفة.",
        "اكتب مثلاً: وظائف تسويق أو كيف أقدم على وظيفة."
    ]

    return random.choice(replies)

def guide_brain(message):

    msg = message.lower()

    # كيف أقدم
    if "كيف اقدم" in msg or "طريقة التقديم" in msg:
        return (
            "للتقديم على وظيفة اتبع الخطوات التالية:\n"
            "1️⃣ افتح صفحة الوظائف\n"
            "2️⃣ اختر الوظيفة المناسبة\n"
            "3️⃣ اضغط زر (تقديم)\n"
            "4️⃣ املأ بياناتك\n"
            "5️⃣ ارفع السيرة الذاتية إن وجدت\n"
            "6️⃣ اضغط إرسال الطلب ✅"
        )

    # كيف أنشر وظيفة
    if "كيف انشر" in msg or "اضف وظيفة" in msg:
        return (
            "لنشر وظيفة:\n"
            "1️⃣ انتقل إلى صفحة (نشر وظيفة)\n"
            "2️⃣ اكتب عنوان الوظيفة\n"
            "3️⃣ أضف الوصف والمتطلبات\n"
            "4️⃣ بيانات التواصل\n"
            "5️⃣ اضغط نشر 🚀"
        )

    return None
    
# =========================
# TOOL DETECTION
# =========================

def detect_tool(message: str):

    msg = message.lower().strip()

    if any(word in msg for word in [
        "اعرض الوظائف",
        "وظائف متاحة",
        "اريد وظائف",
        "show jobs",
        "available jobs"
    ]):
        return "get_jobs"

    if any(word in msg for word in [
        "ابحث عن",
        "search job",
        "وظيفة في"
    ]):
        return "search_jobs"

    if any(word in msg for word in [
        "اضف وظيفة",
        "نشر وظيفة",
        "post job"
    ]):
        return "add_job"

    return None


# =========================
# TOOLS BRAIN
# =========================

def tools_brain(message):

    tool = detect_tool(message)

    if tool == "get_jobs":
        return get_jobs()

    if tool == "search_jobs":
        keyword = message.replace("ابحث عن", "").replace("وظيفة", "").strip()
        return search_jobs(keyword)

    if tool == "add_job":
        return "لإضافة وظيفة انتقل إلى صفحة نشر وظيفة داخل المنصة."

    return None


# =========================
# MAIN AGENT
# =========================

def run_agent(user_id, message, page="home"):

    # 1️⃣ FAQ
    faq_answer = search_faq(message)
    if faq_answer:
        return faq_answer

    # GUIDE BRAIN
    guide_answer = guide_brain(message)
    if guide_answer:
        return guide_answer
    
    # 2️⃣ TOOLS
    tool_answer = tools_brain(message)
    if tool_answer:
        return tool_answer

    # 3️⃣ ONLINE AI
    history = get_memory(user_id)

    prompt = SYSTEM_PROMPT + "\n\n"

    for h in history[-6:]:
        prompt += h + "\n"

    prompt += f"User: {message}\nAssistant:"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 180,
            "temperature": 0.8,
            "do_sample": True
        }
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=15
        )

        output = response.json()

        if isinstance(output, list):
            text = output[0]["generated_text"]
            reply = text.split("Assistant:")[-1].strip()
            reply = reply.replace("User:", "").strip()
            reply = reply[:600]
        else:
            reply = fallback_reply(message)

    except:
        reply = fallback_reply(message)

    save_memory(user_id, f"User: {message}")
    save_memory(user_id, f"Assistant: {reply}")

    return reply
