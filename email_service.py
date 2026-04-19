import os
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from app import query

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_new_job_email(title, category, location):

    subscribers = query(
        "SELECT email FROM subscribers",
        fetchall=True
    )

    if not subscribers:
        print("No subscribers")
        return

    subject = "📢 وظيفة جديدة على منصة حُر"

    body = f"""
تم نشر وظيفة جديدة:

المسمى: {title}
التخصص: {category}
الموقع: {location}

ادخل المنصة الآن للتقديم:
https://hor-platform1.onrender.com
"""

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)

        for sub in subscribers:

            msg = MIMEMultipart()
            msg["From"] = EMAIL_USER
            msg["To"] = sub["email"]

            # ✅ FIX ENCODING HERE
            msg["Subject"] = Header(subject, "utf-8")

            msg.attach(MIMEText(body, "plain", "utf-8"))

            server.sendmail(
                EMAIL_USER,
                sub["email"],
                msg.as_string()
            )

        server.quit()

        print("✅ Email notification sent")

    except Exception as e:
        print("Email error:", e)
