import os
import re
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "jobs_new.db")
UPLOAD_DIR  = os.path.join(BASE_DIR, "static", "uploads", "cvs")
os.makedirs(UPLOAD_DIR, exist_ok=True)

CATEGORIES = ["برمجة", "تصميم", "كتابة", "تسويق", "ترجمة", "فيديو وصوت", "أخرى"]

CATEGORY_ICONS = {
    "برمجة": "💻", "تصميم": "🎨", "كتابة": "✍️",
    "تسويق": "📣", "ترجمة": "🌐", "فيديو وصوت": "🎬", "أخرى": "📁",
}

CURRENCIES = [
    ("ر.س",  "ريال سعودي"),
    ("ر.ي",  "ريال يمني"),
    ("$",    "دولار أمريكي"),
    ("د.إ",  "درهم إماراتي"),
    ("د.ك",  "دينار كويتي"),
    ("د.ب",  "دينار بحريني"),
    ("ر.ع",  "ريال عُماني"),
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
    ("+20",  "🇪🇬 مصر"),
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


# ─── Database helpers ────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()


def allowed_cv(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


def check_verified(job):
    """Auto-verify: job has full contact info + valid email + positive budget."""
    email = (job["email"] or "").strip()
    has_email = bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))
    has_phone = bool((job["phone"] or "").strip())
    has_wa    = bool((job["whatsapp"] or "").strip())
    try:
        has_budget = int(job["budget"]) > 0
    except Exception:
        has_budget = False
    return all([
        bool((job["title"] or "").strip()),
        bool((job["category"] or "").strip()),
        bool((job["description"] or "").strip()),
        has_email, has_phone, has_wa, has_budget,
    ])


def jobs_to_dicts(rows):
    result = []
    for row in rows:
        d = dict(row)
        d["verified"] = check_verified(d)
        result.append(d)
    return result


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT NOT NULL,
            budget      TEXT NOT NULL,
            currency    TEXT NOT NULL DEFAULT 'ر.س',
            category    TEXT NOT NULL,
            employer    TEXT NOT NULL,
            whatsapp    TEXT NOT NULL,
            email       TEXT,
            phone       TEXT,
            website     TEXT,
            location    TEXT,
            status      TEXT DEFAULT 'active',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id        INTEGER NOT NULL,
            name          TEXT NOT NULL,
            phone         TEXT NOT NULL,
            qualification TEXT,
            experience    TEXT,
            skills        TEXT,
            email         TEXT NOT NULL,
            cv_path       TEXT,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safe migrations for new columns
    for col, ctype in [
        ("phone",    "TEXT"),
        ("website",  "TEXT"),
        ("location", "TEXT"),
        ("status",   "TEXT"),
    ]:
        try:
            db.execute(f"ALTER TABLE jobs ADD COLUMN {col} {ctype}")
        except Exception:
            pass

    count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if count == 0:
        sample = [
            ("تصميم شعار احترافي",
             "أحتاج إلى مصمم محترف لإنشاء شعار عصري لشركة ناشئة في مجال التقنية. يجب أن يكون الشعار بسيطاً وقابلاً للتوسع.",
             "500", "ر.س", "تصميم", "محمد العمري",
             "966501234567", "mohammed@example.com", "966501234567", "https://example.com", "الرياض", "active"),
            ("تطوير موقع إلكتروني بـ React",
             "مطلوب مطور واجهة أمامية لبناء موقع متجر إلكتروني باستخدام React وتكامله مع واجهة برمجية موجودة.",
             "3000", "ر.س", "برمجة", "سارة الأحمدي",
             "966509876543", "sara@techco.sa", "966509876543", "", "جدة", "active"),
            ("كتابة محتوى تسويقي",
             "أبحث عن كاتب محتوى متخصص في التسويق الرقمي لكتابة 10 مقالات لمدونة شركتي بأسلوب إبداعي وجذاب.",
             "800", "ر.س", "كتابة", "فيصل القحطاني",
             "966555112233", "faisal@example.com", "966555112233", "https://faisal-blog.com", "الدمام","active"),
        ]
        db.executemany(
            """INSERT INTO jobs
               (title,description,budget,currency,category,employer,
                whatsapp,email,phone,website,location,status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            sample,
        )

    db.commit()
    db.close()

with app.app_context():
    init_db()

# ─── Routes ─────────────────────────────────────────────

@app.route("/")
def index():
    db = get_db()
    cat = request.args.get("category", "")
    total_jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

    if cat:
        rows = db.execute(
            "SELECT * FROM jobs WHERE category=? ORDER BY id DESC", (cat,)
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()

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
        title       = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        budget      = request.form.get("budget", "").strip()
        currency    = request.form.get("currency", "ر.س").strip()
        category    = request.form.get("category", "").strip()
        employer    = request.form.get("employer", "").strip()
        location    = request.form.get("location", "").strip()
        website     = request.form.get("website", "").strip()
        email       = request.form.get("email", "").strip()

        wa_code     = request.form.get("wa_code",    "+966")
        wa_local    = request.form.get("wa_local",   "").strip()
        ph_code     = request.form.get("ph_code",    "+966")
        ph_local    = request.form.get("ph_local",   "").strip()

        wa_digits   = "".join(filter(str.isdigit, wa_code + wa_local))
        ph_digits   = "".join(filter(str.isdigit, ph_code + ph_local)) if ph_local else ""

        if website and not website.startswith(("http://", "https://")):
            website = "https://" + website

        if currency not in [c[0] for c in CURRENCIES]:
            currency = "ر.س"

        errors = []
        if not title:       errors.append("عنوان الوظيفة مطلوب.")
        if not description: errors.append("وصف الوظيفة مطلوب.")
        if not budget or not budget.isdigit():
            errors.append("الميزانية يجب أن تكون رقماً صحيحاً.")
        if not category or category not in CATEGORIES:
            errors.append("يرجى اختيار تصنيف صحيح.")
        if not employer:    errors.append("اسم صاحب العمل مطلوب.")
        if not wa_digits or len(wa_digits) < 9:
            errors.append("رقم الواتساب مطلوب ويجب أن يكون صحيحاً.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "post_job.html",
                categories=CATEGORIES,
                currencies=CURRENCIES,
                arab_codes=ARAB_CODES,
                form=request.form,
            )

        db = get_db()
        db.execute(
            """INSERT INTO jobs
               (title,description,budget,currency,category,employer,
                whatsapp,email,phone,website,location,status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (title, description, budget, currency, category, employer,
             wa_digits, email, ph_digits, website, location,'active'),
        )
        db.commit()
        flash("تم نشر وظيفتك بنجاح! 🎉", "success")
        return redirect(url_for("index"))

    return render_template(
        "post_job.html",
        categories=CATEGORIES,
        currencies=CURRENCIES,
        arab_codes=ARAB_CODES,
        form={},
    )


@app.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
    db  = get_db()
    row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        flash("الوظيفة غير موجودة.", "error")
        return redirect(url_for("index"))

    job      = dict(row)
    verified = check_verified(job)

    name          = request.form.get("name", "").strip()
    applicant_ph  = request.form.get("phone", "").strip()
    qualification = request.form.get("qualification", "").strip()
    experience    = request.form.get("experience", "").strip()
    skills        = request.form.get("skills", "").strip()
    email         = request.form.get("email", "").strip()

    errors = []
    if not name:  errors.append("الاسم مطلوب.")
    if not applicant_ph: errors.append("رقم الهاتف مطلوب.")
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("بريد إلكتروني صحيح مطلوب.")

    cv_path  = None
    cv_file  = request.files.get("cv")
    has_cv   = cv_file and cv_file.filename

    if has_cv:
        if allowed_cv(cv_file.filename):
            ts    = int(datetime.now().timestamp())
            fname = f"{job_id}_{ts}_{secure_filename(cv_file.filename)}"
            cv_file.save(os.path.join(UPLOAD_DIR, fname))
            cv_path = f"uploads/cvs/{fname}"
        else:
            errors.append("يجب أن يكون ملف السيرة الذاتية بصيغة PDF.")
    elif verified:
        errors.append("السيرة الذاتية (PDF) إلزامية لهذه الوظيفة الموثوقة ✅.")

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("index"))

    db.execute(
        """INSERT INTO applications
           (job_id,name,phone,qualification,experience,skills,email,cv_path)
           VALUES (?,?,?,?,?,?,?,?)""",
        (job_id, name, applicant_ph, qualification, experience, skills, email, cv_path),
    )
    db.commit()
    flash(f'تم إرسال طلبك على "{job["title"]}" بنجاح! سيتواصل معك صاحب العمل قريباً. ✅', "success")
    return redirect(url_for("index"))


@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip()
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        flash("يرجى إدخال بريد إلكتروني صحيح.", "error")
        return redirect(url_for("index"))
    db = get_db()
    try:
        db.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        db.commit()
        flash("تم اشتراكك بنجاح! ✅ سنُرسل لك أحدث الوظائف.", "success")
    except sqlite3.IntegrityError:
        flash("هذا البريد الإلكتروني مشترك بالفعل.", "error")
    return redirect(url_for("index"))


# هكذا سيكون شكل الدالة الأخيرة في الكود المدمج
if __name__ == "__main__":
    init_db()
    # جلب المنفذ من النظام أو استخدام 5000 كخيار افتراضي
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)