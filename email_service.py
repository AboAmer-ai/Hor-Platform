import os
import smtplib
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def get_subscribers():

    db = psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require"
    )

    cur = db.cursor()
    cur.execute("SELECT email FROM subscribers")

    emails = [row[0] for row in cur.fetchall()]

    cur.close()
    db.close()

    return emails


def send_new_job_email(title, category, location):

    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    subscribers = get_subscribers()

    if not subscribers:
        print("No subscribers found")
        return

    subject = "وظيفة جديدة في منصة حر 🚀"

    body = f"""
تم نشر وظيفة جديدة:

العنوان: {title}
التصنيف: {category}
الموقع: {location}

ادخل المنصة الآن للتقديم.
"""

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)

    for email in subscribers:
        msg["To"] = email
        server.sendmail(EMAIL_USER, email, msg.as_string())

    server.quit()

    print("✅ Email notification sent")
