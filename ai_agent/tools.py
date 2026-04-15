import os
import psycopg2


# =========================
# DB CONNECTION
# =========================
def get_db():
    conn = psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require"
    )
    conn.autocommit = True
    return conn


# =========================
# GET JOBS
# =========================
def get_jobs():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, employer, location
        FROM jobs
        ORDER BY id DESC
        LIMIT 20
    """)

    jobs = cur.fetchall()

    cur.close()
    conn.close()

    if not jobs:
        return "لا توجد وظائف منشورة حالياً."

    result = []

    for job in jobs:
        title, employer, location = job
        result.append(f"{title} - {employer} - {location}")

    return "\n".join(result)


# =========================
# ADD JOB
# =========================
def add_job(title, company, location, description):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO jobs (title, employer, location, description, budget, currency, category, whatsapp, email, phone, website, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
    """, (
        title,
        company,
        location,
        description,
        "0",
        "ر.س",
        "أخرى",
        "",
        "",
        "",
        ""
    ))

    cur.close()
    conn.close()

    return "✅ تم نشر الوظيفة بنجاح"


# =========================
# SEARCH JOBS
# =========================
def search_jobs(keyword):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, employer
        FROM jobs
        WHERE title ILIKE %s
        ORDER BY id DESC
        LIMIT 20
    """, (f"%{keyword}%",))

    jobs = cur.fetchall()

    cur.close()
    conn.close()

    if not jobs:
        return "لم يتم العثور على نتائج."

    result = []

    for job in jobs:
        title, employer = job
        result.append(f"{title} - {employer}")

    return "\n".join(result)
