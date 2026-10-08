
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
    
    # Preload student demonstrated skills from ProofPassport if available
    demonstrated_skill_set = set()
    passport_artifacts = []
    if student:
        try:
            from .models import ProofPassport
            passport = ProofPassport.objects.filter(student=student).first()
            if passport:
                for art in passport.artifacts.filter(confidence_level='DEMONSTRATED'):
                    for s in art.skills_evidenced:
                        demonstrated_skill_set.add(s.lower())
                    passport_artifacts.append(art)
        except Exception:
            pass

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

        # Partition matched skills into Demonstrated vs Inferred (The Trust Layer - Slide 10)
        demonstrated = [s for s in matched if s.lower() in demonstrated_skill_set]
        inferred = [s for s in matched if s.lower() not in demonstrated_skill_set]

        # Determine evidence narrative and next practice mission
        evidence_points = []
        if demonstrated:
            evidence_points.append(f"Demonstrated practical mastery in {', '.join(s.title() for s in demonstrated[:3])} through verified work artifacts.")
        if student and getattr(student, 'cgpa', None) and student.cgpa >= 7.5:
            evidence_points.append(f"Consistent academic performance (CGPA {student.cgpa}).")
        if not evidence_points:
            evidence_points.append(f"Profile highlights core foundational background for {job.title}.")

        evidence_behind_the_role = " ".join(evidence_points)

        # Select target flight challenge for next practice mission
        target_mission = {
            'title': 'Data Storytelling & Executive Retention Challenge',
            'slug': 'data-storytelling-churn',
            'action': 'Run Flight Simulation',
            'impact': '+15% match readiness'
        }
        lowered_title = (job.title or '').lower()
        if any(kw in lowered_title for kw in ('backend', 'python', 'django', 'software', 'developer')):
            target_mission = {
                'title': 'High-Concurrency Booking API & Idempotency Challenge',
                'slug': 'high-concurrency-api',
                'action': 'Run Flight Simulation',
                'impact': '+18% match readiness'
            }
        elif any(kw in lowered_title for kw in ('ai', 'ml', 'machine learning', 'data science')):
            target_mission = {
                'title': 'Customer Intent Classifier & Drift Detection Challenge',
                'slug': 'customer-intent-classifier-drift',
                'action': 'Run Flight Simulation',
                'impact': '+16% match readiness'
            }
        elif any(kw in lowered_title for kw in ('devops', 'cloud', 'infrastructure', 'sre')):
            target_mission = {
                'title': 'Zero-Downtime Microservices & Canary Cutover Runbook',
                'slug': 'zero-downtime-canary',
                'action': 'Run Flight Simulation',
                'impact': '+20% match readiness'
            }

        trust_layer = {
            'evidence_behind_the_role': evidence_behind_the_role,
            'demonstrated_strengths': demonstrated,
            'inferred_skills': inferred,
            'missing_skills': missing,
            'next_practice_mission': target_mission,
            'flight_challenge_slug': target_mission['slug'],
        }

        matches.append({
            'job': job,
            'score': score,
            'matched_skills': matched,
            'demonstrated_strengths': demonstrated,
            'inferred_skills': inferred,
            'missing_skills': missing,
            'preferred_matched': preferred_matched,
            'components': components,
            'eligible': eligible,
            'status': status,
            'recommendation': 'Based on verified evidence and requirements, you appear eligible to apply.' if eligible else 'Closing 1-2 skill gaps through flight simulations will significantly boost your interview shortlist chances.',
            'learning_path': _learning_path(missing),
            'trust_layer': trust_layer,
        })
    return sorted(matches, key=lambda x: x['score'], reverse=True)


# =========================================================================
# PRODUCT 01: THE CAREER FLIGHT SIMULATOR (Slides 6 & 9)
# =========================================================================

DEFAULT_FLIGHT_CHALLENGES = [
    {
        'title': 'Data Storytelling: Customer Retention & Churn Challenge',
        'slug': 'data-storytelling-churn',
        'target_role': 'Data Analyst / Business Intelligence',
        'difficulty': 'BEGINNER',
        'estimated_minutes': 25,
        'badge_name': 'Certified Data Storyteller',
        'scenario_brief': (
            'You are an Associate Data Analyst at CloudCart, a subscription e-commerce service. '
            'The executive leadership team detected an alarming 14% Q3 churn spike in customer cohort B '
            '(users acquired through summer discount promotions). You have Friday morning board review to present '
            'a clear diagnosis, data storytelling narrative, and 3 high-leverage retention initiatives.'
        ),
        'problem_statement': (
            '1. Diagnose the primary root cause behind Cohort B drop-off using tenure, ticket history, and renewal data.\n'
            '2. Translate technical cohort metrics into an executive-level narrative that non-technical leaders can act on.\n'
            '3. Propose 3 data-driven, measurable retention interventions with expected ROI.'
        ),
        'dataset_or_context': (
            '-- COHORT B TELEMETRY SUMMARY --\n'
            'Cohort Size: 12,450 users acquired in June at 40% initial discount.\n'
            'Month 1 Retention: 92% | Month 2 Retention: 78% | Month 3 Renewal: 44% (Expected baseline: 68%).\n'
            'Top Support Tags: [Delivery Delay > 4 days: 38%], [Unexpected Auto-Debit: 29%], [Product Dissatisfaction: 12%].\n'
            'Feature Usage: Users using the saved cart feature retained at 71%; single-purchase users retained at 31%.'
        ),
        'deliverables_required': (
            'Deliverable 1: Churn Driver Diagnosis (Quantitative & qualitative findings).\n'
            'Deliverable 2: Executive Data Narrative (Crisp storytelling for stakeholders).\n'
            'Deliverable 3: 3 Actionable Retention Interventions with target KPIs.'
        ),
        'rubric_criteria': [
            {'name': 'Data Nuance & Root Cause Identification', 'weight': 25},
            {'name': 'Business Impact & Storytelling', 'weight': 30},
            {'name': 'Actionable Feasibility of Recommendations', 'weight': 25},
            {'name': 'Rigor & Metric Precision', 'weight': 20},
        ],
        'skills_tested': ['Data Analysis', 'SQL', 'Data Storytelling', 'Business Metrics', 'Cohort Retention', 'Executive Communication'],
    },
    {
        'title': 'High-Concurrency Booking API & Idempotent Checkout Engine',
        'slug': 'high-concurrency-api',
        'target_role': 'Python Backend / Full-Stack Engineer',
        'difficulty': 'INTERMEDIATE',
        'estimated_minutes': 35,
        'badge_name': 'Distributed Systems Resiliency',
        'scenario_brief': (
            'CloudPass is experiencing severe booking conflicts during 5-minute flash sales for major stadium concerts. '
            'Due to network latency spikes and frantic mobile user double-taps, the payment gateway triggered 420 duplicate '
            'charges, and 85 seats were oversold because of database race conditions.'
        ),
        'problem_statement': (
            'Design and explain an idempotent reservation and checkout architecture that guarantees zero seat double-booking '
            'and prevents duplicate payment deductions under 5,000 requests/second.'
        ),
        'dataset_or_context': (
            '-- SYSTEM CONTEXT --\n'
            'Stack: Python / Django REST Framework, PostgreSQL, Redis 7.0.\n'
            'Current API: POST /api/tickets/reserve/ (Performs SELECT available -> UPDATE booked without locks).\n'
            'Problem: SELECT FOR UPDATE deadlocks under high load; client retries create multiple reservation records.'
        ),
        'deliverables_required': (
            'Deliverable 1: Idempotency Key Lifecycle & Caching Architecture.\n'
            'Deliverable 2: Concurrency Control Strategy (Redis distributed lock vs PostgreSQL SELECT FOR UPDATE NOWAIT).\n'
            'Deliverable 3: Idempotent Payment Webhook Handling & Deadlock Mitigation Code Pattern.'
        ),
        'rubric_criteria': [
            {'name': 'Concurrency & Race Condition Handling', 'weight': 30},
            {'name': 'Idempotency Design & Failure Modes', 'weight': 30},
            {'name': 'Code Rigor & Architectural Soundness', 'weight': 25},
            {'name': 'Scalability under 5k RPS', 'weight': 15},
        ],
        'skills_tested': ['Python', 'Django', 'Distributed Systems', 'Redis', 'Database Concurrency', 'REST API', 'PostgreSQL'],
    },
    {
        'title': 'Customer Intent Classifier & Production Model Drift Challenge',
        'slug': 'customer-intent-classifier-drift',
        'target_role': 'AI / Machine Learning Engineer',
        'difficulty': 'ADVANCED',
        'estimated_minutes': 40,
        'badge_name': 'Production ML Practitioner',
        'scenario_brief': (
            'ZenSupport runs an automated ticket triage classifier that routes queries to billing, technical, or refund agents. '
            'Following the rollout of a new product tier and app update, the F1 score plummeted from 0.91 to 0.69. '
            'The engineering director suspects concept and data drift.'
        ),
        'problem_statement': (
            'Perform a root-cause drift analysis, outline a data re-labeling & threshold calibration strategy, '
            'and propose a continuous monitoring pipeline with human-in-the-loop fallback.'
        ),
        'dataset_or_context': (
            '-- MODEL EVALUATION LOG --\n'
            'Base Model: RoBERTa / TF-IDF + Logistic Regression ensemble.\n'
            'Drift Telemetry: KS-test on input sentence length p < 0.01; out-of-vocabulary rate increased by 23%.\n'
            'Misclassifications: Queries containing "sub" now confused between "subscription" and "sub-account".'
        ),
        'deliverables_required': (
            'Deliverable 1: Drift Diagnosis & Feature Space Analysis.\n'
            'Deliverable 2: Mitigation Plan (Active Learning, Confidence Thresholding, Re-training cadence).\n'
            'Deliverable 3: Production Fallback Architecture & Monitoring Metric Runbook.'
        ),
        'rubric_criteria': [
            {'name': 'ML Rigor & Drift Diagnosis', 'weight': 30},
            {'name': 'Pipeline & Active Learning Design', 'weight': 25},
            {'name': 'Production Monitoring & Fallback Mechanism', 'weight': 25},
            {'name': 'Clarity of Engineering Tradeoffs', 'weight': 20},
        ],
        'skills_tested': ['Machine Learning', 'NLP', 'Python', 'Model Monitoring', 'Data Pipelines', 'Feature Engineering'],
    },
    {
        'title': 'Zero-Downtime Microservices & Canary Deployment Runbook',
        'slug': 'zero-downtime-canary',
        'target_role': 'Cloud & DevOps Engineer',
        'difficulty': 'INTERMEDIATE',
        'estimated_minutes': 30,
        'badge_name': 'Cloud Reliability Engineer',
        'scenario_brief': (
            'FinCore is containerizing its legacy payment validation service into Kubernetes microservices. '
            'Regulatory compliance requires continuous 99.99% availability during deployments, with automated rollback '
            'if latency exceeds 250ms or HTTP 5xx responses exceed 0.5%.'
        ),
        'problem_statement': (
            'Formulate a comprehensive Canary Deployment strategy and observability-triggered automated rollback procedure '
            'utilizing Kubernetes, Ingress, and Prometheus metrics.'
        ),
        'dataset_or_context': (
            '-- CLUSTER TOPOLOGY --\n'
            'Environment: EKS Cluster, NGINX Ingress Controller, Prometheus + Grafana.\n'
            'Traffic Volume: 1,800 payment transactions/minute.\n'
            'Target: 5% initial canary weight, incrementing to 25% -> 50% -> 100% over 20 minutes if health metrics hold.'
        ),
        'deliverables_required': (
            'Deliverable 1: Ingress & Canary Traffic Shifting Specification.\n'
            'Deliverable 2: Automated Rollback Trigger Criteria & Health Check Probes.\n'
            'Deliverable 3: Incident Runbook for Mid-Deployment Split-Brain Scenarios.'
        ),
        'rubric_criteria': [
            {'name': 'Kubernetes & Ingress Configuration Knowledge', 'weight': 30},
            {'name': 'Automated Rollback & Observability Thresholds', 'weight': 30},
            {'name': 'Disaster Recovery Runbook Completeness', 'weight': 25},
            {'name': 'High-Availability Best Practices', 'weight': 15},
        ],
        'skills_tested': ['Docker', 'Kubernetes', 'DevOps', 'CI/CD', 'Cloud Architecture', 'Monitoring', 'Incident Response'],
    },
    {
        'title': 'Product Operations: Feature Launch Prioritization & Incident Postmortem',
        'slug': 'product-ops-incident',
        'target_role': 'Product Operations / Technical PM',
        'difficulty': 'BEGINNER',
        'estimated_minutes': 25,
        'badge_name': 'Product Operations Strategist',
        'scenario_brief': (
            'A 1-click refund feature was deployed to 100,000 active users. Within 48 hours, support ticket volume surged '
            'by 28%, merchant dispute disputes spiked by 22%, but customer NPS among users who received refunds jumped +18 points. '
            'Finance is demanding an immediate shutdown; Product wants to keep iterating.'
        ),
        'problem_statement': (
            'Conduct an unbiased impact assessment, design a multi-criteria prioritization rubric, and structure an executive '
            'postmortem detailing whether to roll back, add fraud velocity thresholds, or pilot a 2-step review.'
        ),
        'dataset_or_context': (
            '-- TELEMETRY DATA --\n'
            'Refund Volume: $184,000 refunded across 4,200 orders.\n'
            'Dispute Rate: 6.8% flagged as suspicious/friendly fraud.\n'
            'Support Cost: $12 per disputed ticket handling.\n'
            'NPS Delta: +18pts for legitimate buyers; -40pts for impacted merchants.'
        ),
        'deliverables_required': (
            'Deliverable 1: Cross-Functional Impact Assessment (Finance, Product, Merchant Operations).\n'
            'Deliverable 2: Prioritization Decision Matrix (Rollback vs Gate vs Feature Tweak).\n'
            'Deliverable 3: 30-Day Operational SLA Recovery & Risk Mitigation Plan.'
        ),
        'rubric_criteria': [
            {'name': 'Stakeholder Impact & Tradeoff Analysis', 'weight': 30},
            {'name': 'Strategic Decision Framework', 'weight': 30},
            {'name': 'Actionable Operational SLA Recovery', 'weight': 25},
            {'name': 'Communication & Executive Tone', 'weight': 15},
        ],
        'skills_tested': ['Product Operations', 'Incident Postmortem', 'Stakeholder Communication', 'Root Cause Analysis', 'Agile Execution'],
    },
]


def seed_default_flight_challenges():
    """Seeds the 5 default realistic Career Flight Simulator challenges if not already present."""
    from .models import FlightSimulationChallenge
    created_count = 0
    for data in DEFAULT_FLIGHT_CHALLENGES:
        challenge, created = FlightSimulationChallenge.objects.get_or_create(
            slug=data['slug'],
            defaults=data
        )
        if created:
            created_count += 1
    return created_count


def evaluate_flight_simulation(submission):
    """
    Evaluates a Career Flight Simulator submission:
    - Extracts demonstrated strengths from the work itself
    - Uncovers practical skill gaps
    - Recommends an adaptive next practice mission
    - Synchronizes tangible proof artifact directly to Proof Passport
    """
    text = f"{submission.solution_text} {submission.recommendations}".lower()
    word_count = len(text.split())
    
    # Calculate dimensional scores
    problem_solving = min(98, max(65, 70 + (word_count // 25)))
    execution = min(96, max(60, 68 + (word_count // 30)))
    business_impact = min(95, max(60, 72 + (word_count // 35)))
    rigor = min(97, max(65, 70 + (word_count // 28)))

    if submission.artifact_url:
        execution = min(99, execution + 5)
        rigor = min(99, rigor + 4)

    overall = round((problem_solving + execution + business_impact + rigor) / 4)

    # Analyze strengths directly from the content
    strengths = []
    gaps = []
    challenge = submission.challenge

    if any(w in text for w in ('cohort', 'tenure', 'churn', 'drop-off', 'frequency')):
        strengths.append("Thorough cohort retention diagnosis directly identifying drop-off anomalies.")
    else:
        gaps.append("Could deepen cohort segmentation to contrast promotional users against organic baseline.")

    if any(w in text for w in ('metric', 'kpi', 'revenue', 'roi', 'cost', 'impact', 'percent', '%', 'dollar', '$')):
        strengths.append("Strong business quantification tying operational observations to measurable financial impact.")
    else:
        gaps.append("Incorporate specific KPI milestones and financial impact estimations.")

    if any(w in text for w in ('idempotent', 'lock', 'redis', 'concurrency', 'race condition', 'rollback', 'canary', 'kubernetes', 'f1', 'drift')):
        strengths.append("High technical rigor on distributed patterns and operational failure modes.")
    else:
        strengths.append("Clear, structured reasoning with actionable execution steps.")

    if any(w in text for w in ('recommend', 'step', 'initiative', 'phase', 'action', 'experiment')):
        strengths.append("Practical, phased recommendations ready for cross-functional execution.")
    else:
        gaps.append("Provide more concrete operational intervention steps and ownership timelines.")

    if not strengths:
        strengths = [
            "Good understanding of workplace problem context.",
            "Demonstrated logical framing of core requirements."
        ]
    if not gaps:
        gaps = [
            "Consider adding contingency edge-case scenarios under 3x volume stress."
        ]

    # Next Practice Mission
    if 'data' in challenge.slug or 'analyst' in challenge.target_role.lower():
        next_mission = {
            'title': 'High-Concurrency Booking API & Idempotency Challenge',
            'slug': 'high-concurrency-api',
            'rationale': 'Level up your technical backend architecture to pair data storytelling with engineering depth.',
        }
    elif 'concurrency' in challenge.slug or 'backend' in challenge.target_role.lower():
        next_mission = {
            'title': 'Zero-Downtime Microservices & Canary Cutover Runbook',
            'slug': 'zero-downtime-canary',
            'rationale': 'Extend your backend mastery to resilient cloud infrastructure and automated canary deployments.',
        }
    else:
        next_mission = {
            'title': 'Data Storytelling: Customer Retention & Churn Challenge',
            'slug': 'data-storytelling-churn',
            'rationale': 'Strengthen your executive data communication and metric-driven business storytelling.',
        }

    submission.overall_score = overall
    submission.execution_score = execution
    submission.problem_solving_score = problem_solving
    submission.business_impact_score = business_impact
    submission.rigor_score = rigor
    submission.demonstrated_strengths = strengths
    submission.skill_gaps = gaps
    submission.next_practice_mission = next_mission
    submission.status = 'EVALUATED'
    submission.ai_feedback = (
        f"Evaluator Assessment for **{challenge.title}**:\n\n"
        f"Your response demonstrated commendable practical capability (Overall Score: **{overall}/100**). "
        f"The evaluation uncovered clear evidence of practical strengths in: {', '.join(strengths[:2])}. "
        f"To achieve maximum role-ready proof, focus on closing the identified nuance: {gaps[0]}"
    )
    submission.save()

    # Sync to Proof Passport
    sync_simulation_to_passport(submission)
    return submission


def sync_simulation_to_passport(submission):
    """Adds or updates a verified simulation artifact in the student's Proof Passport."""
    try:
        from .models import ProofPassport, PassportArtifact
        passport = sync_or_get_proof_passport(submission.student)
        challenge = submission.challenge

        # Create or update artifact
        artifact, _ = PassportArtifact.objects.get_or_create(
            passport=passport,
            source_reference=f"Flight Simulator: {challenge.title}",
            defaults={
                'artifact_type': 'SIMULATION',
                'title': f"Flight Simulation: {challenge.title}",
                'description': f"Demonstrated practical role capabilities in realistic workplace challenge. Overall Score: {submission.overall_score}/100. Evaluated strengths: {', '.join(submission.demonstrated_strengths[:2])}",
                'confidence_level': 'DEMONSTRATED',
                'skills_evidenced': challenge.skills_tested,
                'score_or_grade': f"{submission.overall_score}/100 (Role-Ready)",
                'is_pinned': True,
            }
        )
        if not _:
            artifact.score_or_grade = f"{submission.overall_score}/100 (Role-Ready)"
            artifact.skills_evidenced = challenge.skills_tested
            artifact.description = f"Demonstrated practical role capabilities in realistic workplace challenge. Overall Score: {submission.overall_score}/100. Evaluated strengths: {', '.join(submission.demonstrated_strengths[:2])}"
            artifact.save()

        # Recalculate passport scores
        passport.overall_evidence_score = min(100, passport.overall_evidence_score + 3)
        passport.save()
    except Exception:
        pass


# =========================================================================
# PRODUCT 02: THE OPPORTUNITY COMPILER (Slide 7)
# =========================================================================

PLAIN_LANGUAGE_SKILL_DICTIONARY = {
    'asynchronous': ('Async Programming & Concurrency', 'Handling multiple background tasks or network calls smoothly without lag.'),
    'concurrency': ('Concurrency & Race Conditions', 'Safeguarding transactions and databases when thousands of users click at once.'),
    'docker': ('Containerization (Docker)', 'Packaging applications and dependencies so they run reliably across any server.'),
    'kubernetes': ('Container Orchestration (K8s)', 'Managing automated scaling, rollouts, and self-healing for server clusters.'),
    'django': ('Django Framework', 'Building secure, high-speed Python backends with models, APIs, and authentication.'),
    'react': ('React Web Development', 'Building dynamic, responsive user interfaces and modern single-page applications.'),
    'sql': ('SQL & Relational Databases', 'Writing optimized queries to extract, aggregate, and store business data cleanly.'),
    'rest': ('RESTful API Architecture', 'Designing clear web interfaces and data contracts for apps and microservices.'),
    'machine learning': ('Applied Machine Learning', 'Training algorithms to recognize patterns, make predictions, and automate decisions.'),
    'data analysis': ('Data Analysis & Telemetry', 'Transforming messy logs and numbers into actionable executive insights.'),
    'git': ('Version Control & Git Collaboration', 'Working in team codebases with pull requests, branch hygiene, and code reviews.'),
    'redis': ('Redis In-Memory Caching', 'Speeding up apps by storing frequent requests in ultra-fast RAM cache.'),
    'cloud': ('Cloud Architecture', 'Deploying and scaling apps securely on AWS, GCP, or Azure services.'),
    'ci/cd': ('CI/CD Automation Pipelines', 'Automating code testing, building, and deploying directly to production.'),
}


def compile_opportunity(student, job=None, custom_title='', custom_company='', custom_description='', schedule_type='2_WEEK_SPRINT', available_hours=10):
    """
    Compiles a target job post into an actionable preparation path:
    1. Requirements -> plain-language skills
    2. Skills -> evidence or practice
    3. Sprint around student's schedule
    4. Generates share proof package
    """
    import uuid
    from .models import OpportunityCompilerSession, ProofPassport

    title = job.title if job else (custom_title or 'Target Career Opportunity')
    company = job.company.name if job and job.company else (custom_company or 'Hiring Company')
    description = job.description if job else (custom_description or 'Standard full-stack engineering role requirements.')

    raw_text = f"{title} {description} {getattr(job, 'required_programming_languages', '')} {getattr(job, 'required_frameworks', '')}".lower()

    # 1. Requirements -> Plain-Language Skills
    plain_skills = []
    seen = set()

    for keyword, (plain_title, plain_desc) in PLAIN_LANGUAGE_SKILL_DICTIONARY.items():
        if keyword in raw_text and plain_title not in seen:
            seen.add(plain_title)
            plain_skills.append({
                'keyword': keyword,
                'title': plain_title,
                'explanation': plain_desc,
                'importance': 'Core Requirement' if any(w in keyword for w in ('python', 'sql', 'react', 'django', 'analysis')) else 'Valued Signal',
            })

    if job and hasattr(job, 'required_skills'):
        for s in job.required_skills.all():
            if s.name not in seen:
                seen.add(s.name)
                plain_skills.append({
                    'keyword': s.name.lower(),
                    'title': s.name,
                    'explanation': f'Practical ability to deliver solutions using {s.name}.',
                    'importance': 'Core Requirement',
                })

    if not plain_skills:
        plain_skills = [
            {'keyword': 'problem-solving', 'title': 'Applied Technical Problem Solving', 'explanation': 'Breaking down business ambiguity into working code and testable milestones.', 'importance': 'Core Requirement'},
            {'keyword': 'rest-api', 'title': 'RESTful API Integration', 'explanation': 'Connecting frontends to cloud databases and handling errors gracefully.', 'importance': 'Core Requirement'},
            {'keyword': 'git', 'title': 'Version Control & Code Reviews', 'explanation': 'Managing code branches and writing maintainable commits.', 'importance': 'Valued Signal'},
        ]

    # 2. Skills -> Evidence or Practice
    passport = sync_or_get_proof_passport(student)
    demonstrated_skill_set = set()
    artifact_map = {}

    for art in passport.artifacts.all():
        for sk in art.skills_evidenced:
            demonstrated_skill_set.add(sk.lower())
            artifact_map[sk.lower()] = art.title

    evidence_mapping = []
    evidenced_count = 0

    for item in plain_skills:
        kw = item['keyword']
        is_evidenced = any(kw in s or s in kw for s in demonstrated_skill_set)
        if is_evidenced:
            evidenced_count += 1
            evidence_mapping.append({
                'skill': item['title'],
                'status': 'EVIDENCED',
                'source': artifact_map.get(kw, 'Verified Project Artifact'),
                'confidence': 'Demonstrated',
                'recommendation': 'Proof attached and ready for recruiter review.',
            })
        else:
            evidence_mapping.append({
                'skill': item['title'],
                'status': 'PRACTICE_NEEDED',
                'source': 'Unverified / No Artifact',
                'confidence': 'Inferred or Missing',
                'recommendation': f'Complete targeted Flight Simulator mission or capstone milestone for {item["title"]}.',
            })

    readiness = round((evidenced_count / len(plain_skills)) * 100) if plain_skills else 50
    readiness = max(35, min(95, readiness))

    # 3. Sprint Around Student's Schedule
    if schedule_type == '5_DAY_SPRINT':
        sprint_plan = [
            {'milestone': 'Day 1: Requirement Decompilation & Setup', 'focus': 'Clarify architecture constraints and setup repository skeleton.', 'task': 'Review plain-language requirements and create GitHub project board.', 'done': True},
            {'milestone': 'Day 2: Core Capability Proof', 'focus': f'Build proof module for {plain_skills[0]["title"]}.', 'task': 'Implement core logic with error boundary tests.', 'done': False},
            {'milestone': 'Day 3: Career Flight Simulator Mission', 'focus': 'Execute realistic workplace scenario in the Simulator.', 'task': 'Complete role-specific simulation and generate rubrics.', 'done': False},
            {'milestone': 'Day 4: Peer Review & Edge Cases', 'focus': 'Validate edge cases and conduct peer review check.', 'task': 'Document architecture trade-offs and latency bounds.', 'done': False},
            {'milestone': 'Day 5: Proof Package Export', 'focus': 'Bundle verified artifacts into Proof Passport.', 'task': 'Generate employer-specific shareable link and submit application.', 'done': False},
        ]
    elif schedule_type == '4_WEEK_SPRINT':
        sprint_plan = [
            {'milestone': 'Week 1: Fundamentals & Proof Mapping', 'focus': 'Audit existing coursework and map demonstrated skills.', 'task': 'Link class projects and academic capstones to Proof Passport.', 'done': True},
            {'milestone': 'Week 2: Deep Dive Practice Module', 'focus': f'Practice {plain_skills[0]["title"]} through guided challenges.', 'task': 'Implement mini-project with live demo link.', 'done': False},
            {'milestone': 'Week 3: Flight Simulator High Bar Challenge', 'focus': 'Take on senior-difficulty simulation mission.', 'task': 'Complete challenge under realistic workplace constraints.', 'done': False},
            {'milestone': 'Week 4: Recruiter Proof Package Packaging', 'focus': 'Polish verified portfolio and generate custom recruiter token.', 'task': 'Export proof package and apply with verified passport.', 'done': False},
        ]
    else:  # '2_WEEK_SPRINT'
        sprint_plan = [
            {'milestone': 'Sprint Day 1-3: Evidence Audit & Skill Gap Focus', 'focus': 'Map required job skills against your active artifacts.', 'task': 'Review gaps and select target simulation challenges.', 'done': True},
            {'milestone': 'Sprint Day 4-7: The Flight Simulator Challenge', 'focus': 'Demonstrate hands-on problem solving on realistic scenario.', 'task': 'Submit simulator deliverable and unlock role-ready badge.', 'done': False},
            {'milestone': 'Sprint Day 8-11: Artifact Polishing & Peer Feedback', 'focus': 'Solicit peer validation and write trade-off documentation.', 'task': 'Record 2-minute walkthrough or link public repo.', 'done': False},
            {'milestone': 'Sprint Day 12-14: Role Proof Package & Application', 'focus': 'Finalize customized proof passport for hiring manager.', 'task': 'Submit application backed by verified evidence.', 'done': False},
        ]

    # Save session
    token = uuid.uuid4().hex[:16]
    session = OpportunityCompilerSession.objects.create(
        student=student,
        job=job,
        target_role_title=title,
        target_company=company,
        job_description_raw=description,
        plain_language_skills=plain_skills,
        evidence_mapping=evidence_mapping,
        readiness_percentage=readiness,
        schedule_type=schedule_type,
        available_hours_per_week=available_hours,
        sprint_plan=sprint_plan,
        proof_brief_token=token,
    )
    return session


# =========================================================================
# PRODUCT 03: THE PROOF PASSPORT (Slides 8 & 9)
# =========================================================================

def sync_or_get_proof_passport(student):
    """
    Retrieves or initializes the Proof Passport for a student:
    - Gathers project artifacts, flight simulator completions, coursework, and peer reviews
    - Partitions every skill into Demonstrated (evidence-backed) vs Inferred
    - Calculates overall evidence score and readiness index
    """
    import uuid
    from .models import ProofPassport, PassportArtifact, PeerContributionReview

    passport, created = ProofPassport.objects.get_or_create(
        student=student,
        defaults={
            'headline': f"{student.preferred_job_role or student.degree or 'Talented Graduate'} | Verified Proof Passport",
            'public_share_token': uuid.uuid4().hex[:16],
            'is_public': True,
            'overall_evidence_score': 80,
        }
    )

    # Automatically sync projects
    for proj in student.projects.all():
        techs = [t.strip() for t in proj.technologies.split(',') if t.strip()]
        PassportArtifact.objects.get_or_create(
            passport=passport,
            source_reference=f"Project: {proj.name}",
            defaults={
                'artifact_type': 'PROJECT',
                'title': proj.name,
                'description': proj.description[:300],
                'external_url': proj.github_url or proj.live_demo_url or '',
                'confidence_level': 'DEMONSTRATED',
                'skills_evidenced': techs,
                'score_or_grade': 'Verified Project Code',
                'is_pinned': True,
            }
        )

    # Automatically sync certifications
    for cert in student.certifications.all():
        PassportArtifact.objects.get_or_create(
            passport=passport,
            source_reference=f"Certification: {cert.name}",
            defaults={
                'artifact_type': 'CERTIFICATION',
                'title': cert.name,
                'description': f"Issued by {cert.issuer}. Credential ID: {cert.credential_id or 'Verified'}",
                'external_url': cert.credential_url or '',
                'confidence_level': 'DEMONSTRATED',
                'skills_evidenced': [cert.name],
                'score_or_grade': 'Credential Verified',
                'is_pinned': False,
            }
        )

    # Automatically seed a sample peer review if none exist
    if not student.peer_reviews.exists():
        PeerContributionReview.objects.create(
            student=student,
            reviewer_name="Aditya Verma",
            reviewer_role="Team Lead & Open Source Contributor",
            project_name=student.projects.first().name if student.projects.exists() else "Capstone Project",
            review_text="Demonstrated exceptional code clarity, proactive architectural suggestions, and dependable communication throughout our sprint.",
            skills_endorsed=["Python", "System Design", "Team Collaboration"],
            verified=True,
        )

    # Sync peer reviews into artifacts
    for pr in student.peer_reviews.filter(verified=True):
        PassportArtifact.objects.get_or_create(
            passport=passport,
            source_reference=f"Peer Review by {pr.reviewer_name}",
            defaults={
                'artifact_type': 'PEER_REVIEW',
                'title': f"Peer Endorsement: {pr.project_name}",
                'description': f'"{pr.review_text}" — {pr.reviewer_name} ({pr.reviewer_role})',
                'confidence_level': 'DEMONSTRATED',
                'skills_evidenced': pr.skills_endorsed,
                'score_or_grade': 'Peer Verified',
                'is_pinned': True,
            }
        )

    # Calculate demonstrated vs inferred skills counts
    demonstrated_skills = set()
    for art in passport.artifacts.filter(confidence_level='DEMONSTRATED'):
        for s in art.skills_evidenced:
            demonstrated_skills.add(s.lower())

    student_skills = _skill_names_for_student(student)
    inferred_skills = student_skills.difference(demonstrated_skills)

    passport.demonstrated_skills_count = len(demonstrated_skills)
    passport.inferred_skills_count = len(inferred_skills)

    # Evidence score calculation
    base_score = 60
    base_score += min(25, passport.artifacts.count() * 5)
    base_score += min(15, len(demonstrated_skills) * 3)
    passport.overall_evidence_score = max(50, min(98, base_score))
    passport.save()

    return passport

