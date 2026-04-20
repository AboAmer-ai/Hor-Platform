def os
import smtplib
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# =========================
# GET SUBSCRIBERS
# =========================
def get_subscribers():

    db = psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require"
    )

    cur = db.cursor()
    cur.execute("SELECT email FROM subscribers")

    emails = [row[0] for row in cur.fetchall() if row[0]]

    cur.close()
    db.close()

    return emails


# =========================
# CLEAN TEXT (important for Arabic hidden chars)
# =========================
def clean_text(text):
    if not text:
        return ""

    # إزالة رموز الاتجاه المخفية RTL/LTR
    return (
        str(text)
        .replace("\u200f", "")
        .replace("\u200e", "")
        .strip()
    )


# =========================
# SEND EMAIL TO ALL SUBSCRIBERS
# =========================
def send_new_job_email(title, category, location):

    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    subscribers = get_subscribers()

    if not subscribers:
        print("No subscribers found")
        return

    subject = "📢 وظيفة جديدة في منصة حُر"

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

        # 🔥 مهم: خارج اللوب
        server.quit()

        print("✅ Email notification sent to all subscribers")

    except Exception as e:
        print("Email error:", e)
