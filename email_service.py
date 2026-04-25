import os
import smtplib
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require"
    )


# =========================
# CLEAN SUBSCRIBERS DATABASE
# =========================
def clean_subscribers_db():

    db = get_db_connection()
    cur = db.cursor()

    cur.execute("SELECT id, email FROM subscribers")
    rows = cur.fetchall()

    fixed = 0

    for row_id, email in rows:

        if not email:
            continue

        cleaned = (
            str(email)
            .replace("\u200f", "")
            .replace("\u200e", "")
            .replace("\xa0", "")
            .strip()
        )

        if cleaned != email:
            cur.execute(
                "UPDATE subscribers SET email=%s WHERE id=%s",
                (cleaned, row_id)
            )
            fixed += 1

    db.commit()
    cur.close()
    db.close()

    print(f"✅ Cleaned {fixed} subscriber emails")


# =========================
# GET SUBSCRIBERS
# =========================
def get_subscribers():

    db = get_db_connection()
    cur = db.cursor()

    cur.execute("SELECT email FROM subscribers")

    emails = [
        row[0].strip()
        for row in cur.fetchall()
        if row[0]
    ]

    cur.close()
    db.close()

    return emails


# =========================
# CLEAN TEXT (Arabic Fix)
# =========================
def clean_text(text):

    if not text:
        return ""

    return (
        str(text)
        .replace("\u200f", "")
        .replace("\u200e", "")
        .replace("\xa0", "")
        .strip()
    )


# =========================
# SEND EMAIL FUNCTION
# =========================
def send_new_job_email(title, category, location):

    # تنظيف قاعدة البيانات قبل الإرسال
    clean_subscribers_db()

    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    subscribers = get_subscribers()

    if not subscribers:
        print("No subscribers found")
        return

    subject = "📢 وظيفة جديدة في منصة حر"

    body = f"""
تم نشر وظيفة جديدة في المنصة

العنوان: {clean_text(title)}
التصنيف: {clean_text(category)}
الموقع: {clean_text(location)}

ادخل المنصة الآن للتقديم 🚀
"""

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)

        for email in subscribers:

            print("SENDING TO:", repr(email))

            msg = MIMEMultipart()
            msg["From"] = EMAIL_USER
            msg["To"] = email
            msg["Subject"] = Header(subject, "utf-8")

            msg.attach(MIMEText(body, "plain", "utf-8"))

            server.sendmail(
                EMAIL_USER,
                email,
                msg.as_bytes()
            )

        server.quit()

        print("✅ Email notification sent")

    except Exception as e:
        print("Email error:", e)
