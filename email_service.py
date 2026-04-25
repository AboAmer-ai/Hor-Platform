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
# CLEAN TEXT
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
# SEND SINGLE EMAIL
# =========================
def send_email(to_email, subject, body):

    SMTP_SERVER = os.environ.get("SMTP_SERVER")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

    subject = clean_text(subject)
    body = clean_text(body)
    to_email = clean_text(to_email)

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")

    msg.attach(MIMEText(body, "html", "utf-8"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)

        server.sendmail(
            SMTP_USER,
            to_email,
            msg.as_string()
        )

        server.quit()

        print(f"✅ Sent to {to_email}")

    except Exception as e:
        print(f"❌ Failed {to_email} -> {e}")


# =========================
# SEND CAMPAIGN
# =========================
def send_campaign(subject, body):

    print("🚀 Starting campaign...")

    clean_subscribers_db()

    subscribers = get_subscribers()

    print(f"📨 Subscribers count: {len(subscribers)}")

    for email in subscribers:
        send_email(email, subject, body)

    print("✅ Campaign finished")
