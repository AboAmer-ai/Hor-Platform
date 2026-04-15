from app import db


def get_jobs():

    jobs = Job.query.all()

    if not jobs:
        return "لا توجد وظائف منشورة حالياً."

    result = []

    for job in jobs:
        result.append(
            f"{job.title} - {job.company} - {job.location}"
        )

    return "\n".join(result)


def add_job(title, company, location, description):

    new_job = Job(
        title=title,
        company=company,
        location=location,
        description=description
    )

    db.session.add(new_job)
    db.session.commit()

    return "✅ تم نشر الوظيفة بنجاح"


def search_jobs(keyword):

    jobs = Job.query.filter(
        Job.title.contains(keyword)
    ).all()

    if not jobs:
        return "لم يتم العثور على نتائج."

    result = []

    for job in jobs:
        result.append(
            f"{job.title} - {job.company}"
        )

    return "\n".join(result)
