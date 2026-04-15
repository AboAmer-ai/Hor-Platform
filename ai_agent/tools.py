from flask import current_app

def create_job(data):
    db = current_app.query

    db("""
        INSERT INTO jobs
        (title,description,budget,currency,category,employer,
         whatsapp,email,phone,website,location,status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active')
    """, (
        data["title"],
        data["description"],
        data["budget"],
        "ر.س",
        data["category"],
        data["employer"],
        data["whatsapp"],
        data["email"],
        "",
        "",
        ""
    ))

    return "تم نشر الوظيفة بنجاح"
