
import re
import zipfile
from io import BytesIO

from django.conf import settings

from .models import ResumeAnalysis
from students.models import Skill, StudentSkill

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from docx import Document
except ImportError:  # pragma: no cover - deployment dependency check handles this
    Document = None


KNOWN_SKILLS = {
    'python', 'django', 'flask', 'fastapi', 'java', 'spring boot', 'javascript',
    'typescript', 'react', 'node.js', 'sql', 'postgresql', 'mysql', 'mongodb',
    'redis', 'docker', 'kubernetes', 'aws', 'azure', 'git', 'rest api', 'html',
    'css', 'machine learning', 'data analysis', 'pandas', 'numpy', 'tensorflow',
    'pytorch', 'hibernate', 'graphql', 'c++', 'c#', 'go',
}


def _csv_values(value):
    return [item.strip() for item in re.split(r'[,\n;|]+', value or '') if item.strip()]


def extract_resume_text(upload):
    """Extract text from a PDF or DOCX without exposing the uploaded file."""
    extension = upload.name.rsplit('.', 1)[-1].lower() if upload and '.' in upload.name else ''
    upload.seek(0)
    data = upload.read()
    upload.seek(0)
    text = ''
    if extension == 'pdf':
        if fitz is not None:
            try:
                with fitz.open(stream=data, filetype='pdf') as document:
                    text = '\n'.join(page.get_text() for page in document).strip()
            except Exception:
                text = ''
        if not text and pypdf is not None:
            try:
                reader = pypdf.PdfReader(BytesIO(data))
                text = '\n'.join(page.extract_text() or '' for page in reader.pages).strip()
            except Exception:
                text = ''
        if not text and fitz is None and pypdf is None:
            raise ValueError('PDF parsing is unavailable. Please install PyMuPDF or pypdf.')
    elif extension == 'docx':
        if Document is not None:
            try:
                document = Document(BytesIO(data))
                text = '\n'.join(paragraph.text for paragraph in document.paragraphs).strip()
            except Exception:
                text = ''
        if not text:
            try:
                import xml.etree.ElementTree as ET
                with zipfile.ZipFile(BytesIO(data)) as docx_zip:
                    xml_content = docx_zip.read('word/document.xml')
                    tree = ET.fromstring(xml_content)
                    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    paragraphs = []
                    for p in tree.iterfind('.//w:p', ns):
                        p_text = ''.join(node.text for node in p.iterfind('.//w:t', ns) if node.text)
                        if p_text:
                            paragraphs.append(p_text)
                    text = '\n'.join(paragraphs).strip()
            except Exception:
                text = ''
        if not text and Document is None:
            raise ValueError('DOCX parsing is unavailable. Please install python-docx.')
    else:
        raise ValueError('Upload a PDF or DOCX resume.')
    if not text:
        raise ValueError('No selectable text was found. Please upload a text-based PDF or DOCX resume.')
    return text


def _find_year(text):
    years = [int(value) for value in re.findall(r'\b(19\d{2}|20\d{2})\b', text)]
    return years[-1] if years else None


def analyze_resume_text(text):
    lowered = text.lower()
    detected = sorted({skill.title() for skill in KNOWN_SKILLS if skill in lowered})
    languages = [skill for skill in detected if skill.lower() in {'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go'}]
    frameworks = [skill for skill in detected if skill.lower() in {'django', 'flask', 'fastapi', 'spring boot', 'react', 'node.js', 'tensorflow', 'pytorch'}]
    databases = [skill for skill in detected if skill.lower() in {'sql', 'postgresql', 'mysql', 'mongodb', 'redis'}]
    tools = [skill for skill in detected if skill.lower() in {'docker', 'kubernetes', 'aws', 'azure', 'git'}]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {
        'extracted_name': lines[0][:200] if lines else '',
        'education': '\n'.join(line for line in lines if any(word in line.lower() for word in ('b.tech', 'b.e', 'bsc', 'm.tech', 'degree', 'university', 'college'))),
        'degree': next((line[:160] for line in lines if any(word in line.lower() for word in ('b.tech', 'b.e', 'bsc', 'm.tech', 'computer science'))), ''),
        'college': next((line[:240] for line in lines if 'college' in line.lower() or 'university' in line.lower()), ''),
        'graduation_year': _find_year(text),
        'skills': detected,
        'programming_languages': languages,
        'frameworks': frameworks,
        'databases': databases,
        'tools': tools,
        'certifications': [line for line in lines if 'certif' in line.lower()][:20],
        'projects': [line for line in lines if 'project' in line.lower()][:20],
        'experience': [line for line in lines if any(word in line.lower() for word in ('intern', 'experience', 'developer', 'engineer'))][:20],
        'relevant_keywords': detected,
    }


def analyze_resume_for_student(student, upload=None):
    upload = upload or student.resume
    analysis = ResumeAnalysis.objects.get_or_create(student=student)[0]
    try:
        text = extract_resume_text(upload)
        parsed = analyze_resume_text(text)
        analysis.extracted_text = text
        analysis.ats_score = min(100, 50 + len(parsed['skills']) * 5)
        analysis.analysis_result = parsed
        for field, value in parsed.items():
            if hasattr(analysis, field):
                setattr(analysis, field, value)
        analysis.missing_keywords = ''
        analysis.improvement_suggestions = 'Add measurable outcomes and role-specific keywords.'
        analysis.parse_error = ''
        analysis.save()
        profile_updates = {}
        if parsed['degree'] and not student.degree:
            profile_updates['degree'] = parsed['degree']
        if parsed['college'] and not student.college:
            profile_updates['college'] = parsed['college']
        if parsed['graduation_year'] and not student.graduation_year:
            profile_updates['graduation_year'] = parsed['graduation_year']
        if profile_updates:
            for field, value in profile_updates.items():
                setattr(student, field, value)
            student.save(update_fields=[*profile_updates, 'updated_at'])
        for skill_name in parsed['skills']:
            skill, _ = Skill.objects.get_or_create(name=skill_name)
            StudentSkill.objects.get_or_create(student=student, skill=skill)
        return analysis
    except Exception as exc:
        analysis.parse_error = str(exc)[:300]
        analysis.extracted_text = ''
        analysis.save(update_fields=['parse_error', 'extracted_text', 'analyzed_at'])
        return analysis


def analyze_resume_mock(text):
    """Deterministic mock resume analysis for demo and presentation flows."""
    lowered = (text or '').lower()
    detected = []
    for skill in ['python', 'django', 'sql', 'react', 'javascript', 'java', 'aws', 'docker', 'rest', 'html', 'css', 'dsa']:
        if skill in lowered:
            detected.append(skill.title())
    missing = ['Docker', 'AWS'] if 'docker' not in lowered and 'aws' not in lowered else []
    return {
        'ats_score': 82,
        'skills_score': 88,
        'project_score': 80,
        'keyword_score': 84,
        'detected_skills': detected or ['Python', 'Django', 'SQL'],
        'missing_skills': missing or ['REST API'],
        'missing_keywords': ['Agile', 'CI/CD'],
        'suggestions': ['Add more measurable impact statements to your projects.', 'Highlight backend/API work with specific technologies used.']
    }


def _skill_names_for_student(student):
    if not student:
        return set()
    return {skill.name.lower() for skill in student.skills.all()} if hasattr(student, 'skills') else {item.skill.name.lower() for item in student.studentskill_set.all()}


def _requirement_names(job):
    return {
        'required': {skill.name.lower() for skill in job.required_skills.all()},
        'preferred': {skill.name.lower() for skill in job.preferred_skills.all()},
        'languages': {item.lower() for item in _csv_values(job.required_programming_languages)},
        'frameworks': {item.lower() for item in _csv_values(job.required_frameworks)},
        'technologies': {item.lower() for item in _csv_values(job.required_technologies)},
    }


def _student_experience_years(student):
    return sum((item.end_date - item.start_date).days / 365 for item in student.internships.all() if item.start_date and item.end_date)


def _learning_path(missing):
    paths = {
        'java': 'Core Java', 'spring boot': 'Spring Boot', 'hibernate': 'Hibernate',
        'react': 'React fundamentals', 'docker': 'Docker fundamentals', 'sql': 'SQL and data modeling',
        'rest api': 'REST API design', 'python': 'Python programming',
    }
    return [paths.get(skill, f'{skill.title()} fundamentals') for skill in sorted(missing)]


def calculate_career_readiness(student):
    if not student:
        return 0

    profile_score = 0
    if student.cgpa:
        profile_score += min(int((student.cgpa / 10) * 35), 35)
    if student.department:
        profile_score += 10
    if student.location:
        profile_score += 5
    if student.resume:
        profile_score += 15
    if student.profile_photo:
        profile_score += 5

    project_count = student.projects.count() if hasattr(student, 'projects') else 0
    skill_count = len(_skill_names_for_student(student))
    readiness = int(min(100, profile_score + (min(skill_count, 10) * 4) + (project_count * 6)))
    return max(0, min(100, readiness))


def match_jobs(student, jobs):
    matches = []
    student_skills = _skill_names_for_student(student)
    weights = getattr(settings, 'AI_MATCH_WEIGHTS', {'required_skills': 60, 'education': 15, 'cgpa': 10, 'experience': 10, 'preferred_skills': 5})
    for job in jobs:
        if not job:
            continue
        requirements = _requirement_names(job)
        all_required = requirements['required'] | requirements['languages'] | requirements['frameworks'] | requirements['technologies']
        matched = sorted(student_skills.intersection(all_required))
        missing = sorted(all_required.difference(student_skills))
        preferred_matched = sorted(student_skills.intersection(requirements['preferred']))
        education_ok = not job.eligible_degree or job.eligible_degree.lower() in (student.degree or '').lower()
        cgpa_ok = not job.minimum_cgpa or (student.cgpa is not None and student.cgpa >= job.minimum_cgpa)
        experience_ok = not job.experience_required or _student_experience_years(student) >= job.experience_required
        active_weights = []
        components = {}
        required_ratio = len(matched) / len(all_required) if all_required else 1
        components['Required skills'] = round(required_ratio * weights['required_skills'])
        active_weights.append(weights['required_skills'])
        if job.eligible_degree:
            components['Education'] = weights['education'] if education_ok else 0
            active_weights.append(weights['education'])
        if job.minimum_cgpa:
            components['CGPA'] = weights['cgpa'] if cgpa_ok else 0
            active_weights.append(weights['cgpa'])
        if job.experience_required:
            components['Experience'] = weights['experience'] if experience_ok else 0
            active_weights.append(weights['experience'])
        if requirements['preferred']:
            components['Preferred skills'] = round((len(preferred_matched) / len(requirements['preferred'])) * weights['preferred_skills'])
            active_weights.append(weights['preferred_skills'])
        score = round(sum(components.values()) / sum(active_weights) * 100) if active_weights else 0
        eligible = not missing and education_ok and cgpa_ok and experience_ok
        status = 'ELIGIBLE' if eligible else ('PARTIAL MATCH' if score >= 40 else 'NOT CURRENTLY ELIGIBLE')
        matches.append({
            'job': job,
            'score': score,
            'matched_skills': matched,
            'missing_skills': missing,
            'preferred_matched': preferred_matched,
            'components': components,
            'eligible': eligible,
            'status': status,
            'recommendation': 'Based on the available job requirements, you appear eligible to apply.' if eligible else 'You may not meet the currently configured requirements for this role.',
            'learning_path': _learning_path(missing),
        })
    return sorted(matches, key=lambda x: x['score'], reverse=True)
