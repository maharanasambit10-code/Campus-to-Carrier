import io
import re
import zipfile
from xml.etree import ElementTree

from pypdf import PdfReader
from pypdf.errors import PdfReadError, PdfStreamError

from .skill_extractor import extract_skills


def extract_resume_text(uploaded_file):
    """Extract text from a PDF or DOCX upload without sending private resumes to an API."""
    uploaded_file.seek(0)
    extension = uploaded_file.name.lower().rsplit('.', 1)[-1]
    if extension == 'docx':
        try:
            with zipfile.ZipFile(uploaded_file) as document:
                xml = document.read('word/document.xml')
            root = ElementTree.fromstring(xml)
            text = '\n'.join(
                ''.join(node.itertext()).strip()
                for node in root.iter()
                if node.tag.endswith('}p')
            ).strip()
        except (KeyError, OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
            raise ValueError('The uploaded DOCX is not readable.') from exc
        if not text:
            raise ValueError('The uploaded DOCX does not contain readable text.')
        return text

    try:
        reader = PdfReader(io.BytesIO(uploaded_file.read()))
    except (PdfReadError, PdfStreamError) as exc:
        raise ValueError('The uploaded file is not a readable PDF.') from exc
    text = '\n'.join(page.extract_text() or '' for page in reader.pages).strip()
    if not text:
        raise ValueError('The uploaded PDF does not contain readable text.')
    return text


extract_pdf_text = extract_resume_text


def _first_match(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip() if match.lastindex else match.group(0).strip()
    return ''


def _first_line(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip(' :-\t')
    return ''


def analyze_resume_text(text):
    """Produce explainable, deterministic resume analysis suitable for offline demos."""
    skills = extract_skills(text)
    flat_skills = {skill for values in skills.values() for skill in values}
    email = _first_match(text, [r'[\w.+-]+@[\w-]+\.[\w.-]+'])
    phone = _first_match(text, [r'(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)'])
    cgpa_match = re.search(r'\b(?:cgpa|gpa)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    name = next((
        line.strip() for line in text.splitlines()
        if line.strip() and not re.search(
            r'@|\d{7,}|resume|curriculum vitae|objective|education|skills?',
            line,
            re.IGNORECASE,
        )
    ), '')
    department = _first_line(text, [
        r'(?:department|branch|major|stream|speciali[sz]ation)\s*[:\-]\s*(.+)',
    ])
    college = _first_line(text, [
        r'(?:college|university|institute|institution)\s*[:\-]\s*(.+)',
    ])
    graduation_year = _first_match(text, [
        r'(?:graduation|graduated|passing|pass[- ]?out|expected graduation)[^\d]{0,20}(20\d{2})',
    ])
    location = _first_line(text, [r'(?:location|address|city)\s*[:\-]\s*(.+)'])
    sections = {name: bool(re.search(rf'\b{name}\b', text, re.IGNORECASE)) for name in (
        'education', 'project', 'internship', 'certification', 'achievement',
    )}
    required_profile_signals = {
        'email': bool(email),
        'phone': bool(phone),
        'education': sections['education'],
        'projects': sections['project'],
        'experience': sections['internship'],
        'certifications': sections['certification'],
        'achievements': sections['achievement'],
        'technical skills': bool(flat_skills),
    }
    missing_information = [label.title() for label, present in required_profile_signals.items() if not present]
    strengths = []
    if flat_skills:
        strengths.append(f'{len(flat_skills)} normalized technical skills detected.')
    if sections['project']:
        strengths.append('Projects section found.')
    if sections['internship']:
        strengths.append('Internship or experience evidence found.')
    if email and phone:
        strengths.append('Contact information is complete.')
    weaknesses = []
    if not sections['project']:
        weaknesses.append('Add projects with measurable outcomes.')
    if not sections['internship']:
        weaknesses.append('Add internship or practical experience details.')
    if not flat_skills:
        weaknesses.append('Add a dedicated technical skills section.')
    if not email or not phone:
        weaknesses.append('Add a clearly labeled email and phone number.')

    completeness = sum(required_profile_signals.values()) / len(required_profile_signals)
    skill_bonus = min(len(flat_skills), 10) * 3
    ats_score = min(100, round(completeness * 70 + skill_bonus))
    missing_keywords = [keyword for keyword in ('REST API', 'Git', 'Docker', 'SQL') if keyword not in flat_skills]
    return {
        'ats_score': ats_score,
        'extracted': {
            'name': name,
            'email': email,
            'phone': phone,
            'cgpa': cgpa_match.group(1) if cgpa_match else '',
            'department': department,
            'college': college,
            'graduation_year': graduation_year,
            'location': location,
            'sections': sections,
        },
        'skills': skills,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'missing_information': missing_information,
        'missing_keywords': missing_keywords,
        'suggestions': weaknesses[:3] or ['Tailor your resume keywords to the target role.'],
    }
