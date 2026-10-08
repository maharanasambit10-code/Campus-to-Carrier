import re
from io import BytesIO
from students.models import Skill
from ai_engine.services import extract_resume_text

TECH_RECOMMENDATION_GRAPH = {
    'python': ['FastAPI', 'Docker', 'PostgreSQL', 'AWS', 'Pandas'],
    'django': ['REST API', 'PostgreSQL', 'Docker', 'Celery', 'Redis'],
    'react': ['TypeScript', 'Next.js', 'Redux', 'Tailwind CSS', 'Node.js'],
    'javascript': ['React', 'TypeScript', 'Node.js', 'Express', 'Git'],
    'java': ['Spring Boot', 'Microservices', 'Kafka', 'Docker', 'AWS'],
    'spring boot': ['Microservices', 'Kafka', 'PostgreSQL', 'Docker', 'Kubernetes'],
    'c++': ['DSA', 'System Design', 'Multithreading', 'Linux', 'Git'],
    'sql': ['PostgreSQL', 'MySQL', 'Database Design', 'Query Optimization', 'Python'],
    'aws': ['Docker', 'Kubernetes', 'Terraform', 'CI/CD', 'Serverless'],
    'machine learning': ['PyTorch', 'TensorFlow', 'Deep Learning', 'MLOps', 'Pandas'],
    'data science': ['Python', 'SQL', 'Pandas', 'Scikit-learn', 'Tableau'],
    'docker': ['Kubernetes', 'CI/CD', 'Linux', 'DevOps', 'AWS'],
    'kubernetes': ['Docker', 'Helm', 'Terraform', 'CI/CD', 'Cloud Architecture'],
    'dsa': ['Problem Solving', 'System Design', 'Algorithms', 'Competitive Programming'],
}

EXPANDED_SKILL_KEYWORDS = [
    'Python', 'Java', 'C', 'C++', 'C#', 'JavaScript', 'TypeScript',
    'React', 'Node.js', 'Django', 'Spring Boot', 'SQL', 'MySQL', 'MongoDB',
    'PostgreSQL', 'Redis', 'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
    'Machine Learning', 'Data Science', 'Data Analytics', 'Power BI',
    'Tableau', 'DevOps', 'Git', 'DSA', 'AI', 'System Design', 'REST API',
    'FastAPI', 'Flask', 'Go', 'Rust', 'Kafka', 'PyTorch', 'TensorFlow',
    'Deep Learning', 'NLP', 'LLM', 'Linux', 'CI/CD', 'Selenium', 'Testing',
    'HTML', 'CSS', 'Tailwind', 'Next.js', 'Microservices', 'Express',
]


def extract_skills_from_text(text):
    """
    Extracts recognized technical skills from raw resume or description text.
    Handles special symbols like C++, C#, .NET, etc. safely.
    """
    if not text:
        return []
    
    found_skills = set()
    lowered = text.lower()

    for skill in EXPANDED_SKILL_KEYWORDS:
        s_lower = skill.lower()
        if s_lower == 'c++':
            if re.search(r'\bc\+\+', lowered):
                found_skills.add('C++')
        elif s_lower == 'c#':
            if re.search(r'\bc#', lowered):
                found_skills.add('C#')
        elif s_lower == 'c':
            # Strictly match C as a standalone programming language
            if re.search(r'\b(c\s+programming|language\s+c|c\s+language|\bc\b(?=[\s,/|]))', lowered):
                found_skills.add('C')
        elif s_lower in ('ai', 'dsa', 'sql', 'aws', 'gcp', 'nlp', 'llm'):
            if re.search(r'\b' + re.escape(s_lower) + r'\b', lowered):
                found_skills.add(skill)
        else:
            pattern = r'\b' + re.escape(s_lower) + r'\b'
            if re.search(pattern, lowered):
                found_skills.add(skill)

    return sorted(found_skills)


def calculate_resume_job_match(job, resume_file=None, resume_text='', student_profile=None):
    """
    Computes a realistic, transparent Job Match score and skill breakdown:
    - match_percentage (0 to 100)
    - matched_skills (list)
    - missing_skills (list)
    - recommended_skills (list)
    """
    text = resume_text or ''
    if resume_file:
        try:
            text = extract_resume_text(resume_file)
        except Exception:
            text = ''

    candidate_skills = set()
    if text:
        candidate_skills.update(extract_skills_from_text(text))

    # Also blend student profile recorded skills if available
    if student_profile:
        for sk in student_profile.studentskill_set.select_related('skill'):
            candidate_skills.add(sk.skill.name)
        if not text and student_profile.resume:
            try:
                profile_text = extract_resume_text(student_profile.resume)
                candidate_skills.update(extract_skills_from_text(profile_text))
            except Exception:
                pass

    required_skills = job.all_skills_list()
    if not required_skills:
        # Fallback to general skills
        required_skills = ['Software Engineering', 'Problem Solving']

    # Normalize comparison case-insensitively
    candidate_lookup = {s.lower(): s for s in candidate_skills}
    
    matched = []
    missing = []
    
    for req in required_skills:
        req_clean = req.strip()
        req_lower = req_clean.lower()
        if req_lower in candidate_lookup:
            matched.append(req_clean)
        else:
            # Check partial match
            found = False
            for c_lower, c_orig in candidate_lookup.items():
                if c_lower in req_lower or req_lower in c_lower:
                    matched.append(req_clean)
                    found = True
                    break
            if not found:
                missing.append(req_clean)

    total_req = max(len(required_skills), 1)
    match_percentage = min(100, max(15, round((len(matched) / total_req) * 100)))

    # Compute recommended skills to learn
    recommended = set()
    for m in matched:
        m_lower = m.lower()
        if m_lower in TECH_RECOMMENDATION_GRAPH:
            for rec in TECH_RECOMMENDATION_GRAPH[m_lower]:
                if rec.lower() not in candidate_lookup and rec not in required_skills:
                    recommended.add(rec)
    
    # If missing skills exist, highlight top missing skills as high priority recommendations
    for miss in missing[:3]:
        recommended.add(miss)

    recommended_list = sorted(recommended)[:4]
    if not recommended_list:
        recommended_list = ['System Design', 'Docker', 'Cloud Architecture']

    return {
        'match_percentage': match_percentage,
        'matched_skills': matched,
        'missing_skills': missing,
        'recommended_skills': recommended_list,
        'candidate_skills_count': len(candidate_skills),
        'required_skills_count': len(required_skills),
        'candidate_skills': sorted(candidate_skills),
    }
