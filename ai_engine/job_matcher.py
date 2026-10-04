from .skill_extractor import normalized_skill_names


def _student_skill_names(student):
    return normalized_skill_names(', '.join(
        student.studentskill_set.select_related('skill').values_list('skill__name', flat=True)
    ))


def explain_job_match(student, job):
    student_skills = _student_skill_names(student)
    required = {
        normalized: skill.name
        for skill in job.required_skills.all()
        for normalized in normalized_skill_names(skill.name)
    }
    preferred = {
        normalized: skill.name
        for skill in job.preferred_skills.all()
        for normalized in normalized_skill_names(skill.name)
    }
    matched = sorted(required[key] for key in required if key in student_skills)
    missing = sorted(required[key] for key in required if key not in student_skills)
    eligibility_issues = []

    if job.minimum_cgpa and (student.cgpa is None or student.cgpa < job.minimum_cgpa):
        eligibility_issues.append(
            f'CGPA requirement is {job.minimum_cgpa:g}; your CGPA is {student.cgpa or "not set"}.'
        )
    if job.graduation_year and (student.graduation_year is None or student.graduation_year < job.graduation_year):
        eligibility_issues.append(
            f'Graduation year requirement is {job.graduation_year}; your year is {student.graduation_year or "not set"}.'
        )
    if job.allowed_departments and student.department:
        allowed = {item.strip().lower() for item in job.allowed_departments.split(',') if item.strip()}
        if allowed and not any(item in student.department.lower() for item in allowed):
            eligibility_issues.append(f'Department must be one of: {job.allowed_departments}.')
    if job.min_tenth and (student.tenth_percentage is None or student.tenth_percentage < job.min_tenth):
        eligibility_issues.append(f'10th percentage must be at least {job.min_tenth:g}.')
    if job.min_twelfth and (student.twelfth_percentage is None or student.twelfth_percentage < job.min_twelfth):
        eligibility_issues.append(f'12th percentage must be at least {job.min_twelfth:g}.')

    skill_score = (len(matched) / len(required) * 75) if required else 50
    preferred_score = (len(set(preferred).intersection(student_skills)) / len(preferred) * 10) if preferred else 0
    eligibility_score = 15 if not eligibility_issues else 0
    score = min(100, round(skill_score + preferred_score + eligibility_score))
    if eligibility_issues:
        status = 'NOT_ELIGIBLE'
    elif missing:
        status = 'PARTIALLY_ELIGIBLE'
    else:
        status = 'ELIGIBLE'

    recommendation = (
        'Strong match. You can apply.'
        if status == 'ELIGIBLE' else
        'You can apply, but close the listed skill gaps to improve your chances.'
        if status == 'PARTIALLY_ELIGIBLE' else
        'Review the eligibility issues before applying.'
    )
    return {
        'score': score,
        'matched_skills': matched,
        'missing_skills': missing,
        'eligibility_issues': eligibility_issues,
        'status': status,
        'recommendation': recommendation,
    }
