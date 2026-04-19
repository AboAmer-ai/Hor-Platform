import os
import re
import psycopg2
import smtplib

from email import encoders
from email_service import send_new_job_email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g
from werkzeug.utils import secure_filename
from ai_agent.agent import run_agent
from dotenv import load_dotenv
load_dotenv()
from flask import request, jsonify

app = Flask(__name__)

hf_token = os.getenv("HF_TOKEN")

app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "cvs")
os.makedirs(UPLOAD_DIR, exist_ok=True)

CATEGORIES = ["برمجة", "تصميم", "كتابة", "تسويق", "ترجمة", "فيديو وصوت", "أخرى"]

CATEGORY_ICONS = {
    "برمجة": "💻", "تصميم": "🎨", "كتابة": "✍️",
    "تسويق": "📣", "ترجمة": "🌐", "فيديو وصوت": "🎬", "أخرى": "📁",
}

CURRENCIES = [
    ("ر.س", "ريال سعودي"),
    ("ر.ي", "ريال يمني"),
    ("$", "دولار أمريكي"),
    ("د.إ", "درهم إماراتي"),
    ("د.ك", "دينار كويتي"),
    ("د.ب", "دينار بحريني"),
    ("ر.ع", "ريال عُماني"),
]

ARAB_CODES = [
    ("+966", "🇸🇦 السعودية"),
    ("+967", "🇾🇪 اليمن"),
    ("+971", "🇦🇪 الإمارات"),
    ("+965", "🇰🇼 الكويت"),
    ("+973", "🇧🇭 البحرين"),
    ("+974", "🇶🇦 قطر"),
    ("+968", "🇴🇲 عُمان"),
    ("+962", "🇯🇴 الأردن"),
    ("+961", "🇱🇧 لبنان"),
    ("+963", "🇸🇾 سوريا"),
    ("+964", "🇮🇶 العراق"),
    ("+20", "🇪🇬 مصر"),
    ("+218", "🇱🇾 ليبيا"),
    ("+216", "🇹🇳 تونس"),
    ("+213", "🇩🇿 الجزائر"),
    ("+212", "🇲🇦 المغرب"),
    ("+249", "🇸🇩 السودان"),
    ("+252", "🇸🇴 الصومال"),
    ("+222", "🇲🇷 موريتانيا"),
    ("+253", "🇩🇯 جيبوتي"),
    ("+970", "🇵🇸 فلسطين"),
    ("+269", "🇰🇲 جزر القمر"),
]

# ─────────────────────────────
# DB CONNECTION
# ─────────────────────────────

def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            os.environ.get("DATABASE_URL"),
            sslmode="require"
        )
        g.db.autocommit = True
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()


def query(sql, params=None, fetchone=False, fetchall=False):
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(sql, params or ())

    if fetchone:
        return cur.fetchone()
    if fetchall:
        return cur.fetchall()


# ─────────────────────────────
# AUTO DB INIT (NEW)
# ─────────────────────────────

def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        title TEXT,
        description TEXT,
        budget INTEGER,
        currency TEXT,
        category TEXT,
        employer TEXT,
        whatsapp TEXT,
        email TEXT,
        phone TEXT,
        website TEXT,
        location TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        job_id INTEGER,
        name TEXT,
        phone TEXT,
        qualification TEXT,
        experience TEXT,
        skills TEXT,
        email TEXT,
        cv_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscribers (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    print("🔥 DATABASE INITIALIZED")


@app.before_request
def ensure_db():
    if not hasattr(g, "db_initialized"):
        init_db()
        g.db_initialized = True

# ─────────────────────────────
# SMTP Emails
# ─────────────────────────────
# تنظيف النص من الرموز المخفية (مهم جدًا)
        def clean_text(text):
            return str(text).replace("\u200f", "").replace("\u200e", "").strip()

def send_new_job_email(job_title, job_category, job_location):
    try:
        subscribers = query("SELECT email FROM subscribers", fetchall=True)

        if not subscribers:
            return

        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASS")

        subject = f"🔥 وظيفة جديدة: {job_title}"

        body = f"""
تم نشر وظيفة جديدة في منصة حُر 🚀

📌 الوظيفة: {clean_text(job_title)}
📂 التصنيف: {clean_text(job_category)}
📍 الموقع: {clean_text(job_location)}

ادخل المنصة الآن وقدم عليها 💼
"""

        # 🔥 افتح SMTP مرة واحدة فقط
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)

        for sub in subscribers:
            try:
                msg = MIMEMultipart()
                msg["From"] = sender_email
                msg["To"] = sub["email"]
                msg["Subject"] = subject

                msg.attach(MIMEText(body, "plain", "utf-8"))

                raw_msg = msg.as_bytes()

                server.sendmail(sender_email, sub["email"], raw_msg)

            except Exception as inner:
                print("Failed for:", sub["email"], inner)

        server.quit()

        print("✅ Emails sent successfully")

    except Exception as e:
        print("Email error:", e)



# ─────────────────────────────
# HELPERS (بدون أي تعديل)
# ─────────────────────────────

def allowed_cv(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


def check_verified(job):
    email = (job["email"] or "").strip()
    has_email = bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))
    has_phone = bool((job["phone"] or "").strip())
    has_wa = bool((job["whatsapp"] or "").strip())
    try:
        has_budget = int(job["budget"]) > 0
    except:
        has_budget = False

    return all([
        bool(job["title"]),
        bool(job["category"]),
        bool(job["description"]),
        has_email, has_phone, has_wa, has_budget,
    ])


def jobs_to_dicts(rows):
    result = []
    for row in rows:
        d = dict(row)
        d["verified"] = check_verified(d)
        result.append(d)
    return result


# ─────────────────────────────
# ROUTES (بدون أي تغيير)
# ─────────────────────────────

@app.route("/")
def index():
    cat = request.args.get("category", "")

    total_jobs = query("SELECT COUNT(*) FROM jobs", fetchone=True)["count"]

    if cat:
        rows = query(
            "SELECT * FROM jobs WHERE category=%s ORDER BY id DESC",
            (cat,),
            fetchall=True
        )
    else:
        rows = query("SELECT * FROM jobs ORDER BY id DESC", fetchall=True)

    jobs = jobs_to_dicts(rows)

    return render_template(
        "index.html",
        jobs=jobs,
        total_jobs=total_jobs,
        categories=CATEGORIES,
        category_icons=CATEGORY_ICONS,
        selected_category=cat,
    )


@app.route("/post-job", methods=["GET", "POST"])
def post_job():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        budget = request.form.get("budget", "").strip()
        currency = request.form.get("currency", "ر.س").strip()
        category = request.form.get("category", "").strip()
        employer = request.form.get("employer", "").strip()
        location = request.form.get("location", "").strip()
        website = request.form.get("website", "").strip()
        email = request.form.get("email", "").strip()

        wa_code = request.form.get("wa_code", "+966")
        wa_local = request.form.get("wa_local", "").strip()
        ph_code = request.form.get("ph_code", "+966")
        ph_local = request.form.get("ph_local", "").strip()

        wa_digits = "".join(filter(str.isdigit, wa_code + wa_local))
        ph_digits = "".join(filter(str.isdigit, ph_code + ph_local))

        if website and not website.startswith(("http://", "https://")):
            website = "https://" + website

        errors = []
        if not title:
            errors.append("عنوان الوظيفة مطلوب.")
        if not description:
            errors.append("الوصف مطلوب.")
        if not budget.isdigit():
            errors.append("الميزانية غير صحيحة.")
        if category not in CATEGORIES:
            errors.append("تصنيف غير صحيح.")
        if not employer:
            errors.append("اسم صاحب العمل مطلوب.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("post_job.html",
                                   categories=CATEGORIES,
                                   currencies=CURRENCIES,
                                   arab_codes=ARAB_CODES,
                                   form=request.form)

        query("""
            INSERT INTO jobs
            (title,description,budget,currency,category,employer,
             whatsapp,email,phone,website,location,status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active')
        """, (
            title, description, budget, currency, category, employer,
            wa_digits, email, ph_digits, website, location
        ))
        
        try:
            send_new_job_email(title, category, location)
        except Exception as e:
            print("Email notification failed:", e)

        flash("تم نشر الوظيفة بنجاح 🎉", "success")
        return redirect(url_for("index"))

    return render_template(
        "post_job.html",
        categories=CATEGORIES,
        currencies=CURRENCIES,
        arab_codes=ARAB_CODES,
        form={}
    )


@app.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
    row = query("SELECT * FROM jobs WHERE id=%s", (job_id,), fetchone=True)
    if not row:
        flash("الوظيفة غير موجودة", "error")
        return redirect(url_for("index"))

    job = dict(row)

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()

    cv_file = request.files.get("cv")
    cv_path = None

    if cv_file and cv_file.filename:
        if allowed_cv(cv_file.filename):
            ts = int(datetime.now().timestamp())
            fname = f"{job_id}_{ts}_{secure_filename(cv_file.filename)}"
            cv_file.save(os.path.join(UPLOAD_DIR, fname))
            cv_path = f"uploads/cvs/{fname}"

    query("""
        INSERT INTO applications
        (job_id,name,phone,qualification,experience,skills,email,cv_path)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        job_id, name, phone,
        request.form.get("qualification"),
        request.form.get("experience"),
        request.form.get("skills"),
        email, cv_path
    ))

    flash("تم إرسال الطلب بنجاح ✅", "success")
    return redirect(url_for("index"))


@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip()

    try:
        query("INSERT INTO subscribers (email) VALUES (%s)", (email,))
        print("Subscriber saved:", email)
        flash("تم الاشتراك بنجاح", "success")
    except:
        flash("مشترك مسبقاً", "error")

    return redirect(url_for("index"))

# ==============================
# AI AGENT ROUTE
# ==============================

@app.route("/ai", methods=["POST"])
def ai_chat():

    data = request.get_json()

    message = data.get("message", "")
    page = data.get("page", "home")

    reply = run_agent(
        user_id="guest",
        message=message,
        page=page
    )

    return {"reply": reply}


if __name__ == "__main__":
    with app.app_context():
        init_db()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)