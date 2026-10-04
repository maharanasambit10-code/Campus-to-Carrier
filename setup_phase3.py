import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")
TEMPLATES_DIR = BASE_DIR / "templates"
STUDENT_DIR = TEMPLATES_DIR / "student"
RECRUITER_DIR = TEMPLATES_DIR / "recruiter"
OFFICER_DIR = TEMPLATES_DIR / "officer"

for d in [STUDENT_DIR, RECRUITER_DIR, OFFICER_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 1. AI Engine Services Setup (Mock NLP / Scoring for hackathon demo)
ai_services = """
import random

def analyze_resume_mock(text):
    # Dummy logic to simulate AI processing for hackathon
    return {
        "ats_score": random.randint(75, 95),
        "skills_score": random.randint(80, 98),
        "project_score": random.randint(70, 90),
        "keyword_score": random.randint(80, 95),
        "detected_skills": ["Python", "Django", "SQL", "REST API", "Git"],
        "missing_skills": ["Docker", "AWS"],
        "missing_keywords": ["Agile", "CI/CD"],
        "suggestions": ["Add more quantifiable achievements in your projects."]
    }

def calculate_placement_readiness(student):
    # Base on cgpa and skills
    cgpa_score = (student.cgpa / 10.0) * 100 if student.cgpa else 0
    skills_score = min(student.skills.count() * 10, 100)
    readiness = int((cgpa_score * 0.4) + (skills_score * 0.6))
    return min(readiness + 20, 100)  # Boost for demo

def match_jobs(student, jobs):
    # Simple Mock TF-IDF matching simulation
    matches = []
    student_skills = set([s.skill.name.lower() for s in student.studentskill_set.all()])
    for job in jobs:
        job_skills = set([s.name.lower() for s in job.required_skills.all()])
        matched = student_skills.intersection(job_skills)
        missing = job_skills.difference(student_skills)
        score = int((len(matched) / max(len(job_skills), 1)) * 100)
        
        # Boost if CGPA matches
        if student.cgpa and student.cgpa >= job.minimum_cgpa:
            score = min(score + 10, 100)
            
        matches.append({
            "job": job,
            "score": score,
            "matched_skills": list(matched),
            "missing_skills": list(missing),
            "eligible": student.cgpa and student.cgpa >= job.minimum_cgpa
        })
    return sorted(matches, key=lambda x: x['score'], reverse=True)
"""
with open(BASE_DIR / "ai_engine" / "services.py", "w", encoding="utf-8") as f:
    f.write(ai_services)

# 2. Student Dashboard Template
student_dashboard = """
{% extends 'base.html' %}
{% block content %}
<div class="container-fluid">
    <div class="row">
        <!-- Sidebar -->
        <div class="col-md-2 sidebar py-4">
            <h5 class="fw-bold px-3 mb-4 text-primary">Student Panel</h5>
            <ul class="nav flex-column gap-2">
                <li class="nav-item"><a class="nav-link active fw-bold text-dark" href="#"><i class="bi bi-grid me-2"></i> Dashboard</a></li>
                <li class="nav-item"><a class="nav-link text-muted" href="#"><i class="bi bi-person me-2"></i> My Profile</a></li>
                <li class="nav-item"><a class="nav-link text-muted" href="#"><i class="bi bi-search me-2"></i> Find Jobs</a></li>
                <li class="nav-item"><a class="nav-link text-muted" href="#"><i class="bi bi-robot me-2"></i> AI Recommendations</a></li>
                <li class="nav-item"><a class="nav-link text-muted" href="#"><i class="bi bi-file-earmark-text me-2"></i> Resume Analyzer</a></li>
            </ul>
        </div>
        <!-- Main Content -->
        <div class="col-md-10 p-5">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Good Morning, <span class="text-primary fw-bold">Student 👋</span></h2>
            </div>
            
            <div class="row g-4 mb-5">
                <div class="col-md-3">
                    <div class="card p-4 border-start border-primary border-4">
                        <h6 class="text-muted fw-bold">Placement Readiness</h6>
                        <h2 class="fw-bold">87<span class="fs-5 text-muted">/100</span></h2>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card p-4 border-start border-success border-4">
                        <h6 class="text-muted fw-bold">Resume Score</h6>
                        <h2 class="fw-bold text-success">84<span class="fs-5 text-muted">/100</span></h2>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card p-4 border-start border-warning border-4">
                        <h6 class="text-muted fw-bold">AI Job Matches</h6>
                        <h2 class="fw-bold">12</h2>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card p-4 border-start border-danger border-4">
                        <h6 class="text-muted fw-bold">Applications</h6>
                        <h2 class="fw-bold text-danger">8</h2>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-8">
                    <h4 class="fw-bold mb-3">AI Career Intelligence</h4>
                    <div class="card p-4">
                        <h5 class="text-primary fw-bold">YOUR BEST CAREER MATCH</h5>
                        <h3 class="fw-bold mb-3">Python Backend Developer <span class="badge bg-success ms-2 fs-6">94% Match</span></h3>
                        
                        <div class="row mt-4">
                            <div class="col-md-6">
                                <h6 class="fw-bold">Why?</h6>
                                <ul class="list-unstyled">
                                    <li class="text-success"><i class="bi bi-check-circle-fill me-2"></i> Python</li>
                                    <li class="text-success"><i class="bi bi-check-circle-fill me-2"></i> Django</li>
                                    <li class="text-success"><i class="bi bi-check-circle-fill me-2"></i> SQL</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6 class="fw-bold">Missing Skills:</h6>
                                <ul class="list-unstyled">
                                    <li class="text-danger"><i class="bi bi-x-circle-fill me-2"></i> Docker</li>
                                    <li class="text-danger"><i class="bi bi-x-circle-fill me-2"></i> AWS</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <h4 class="fw-bold mb-3">Application Timeline</h4>
                    <div class="card p-4">
                        <ul class="list-unstyled">
                            <li class="mb-3"><span class="badge bg-primary">APPLIED</span> <span class="text-muted ms-2">Tech Innovations Inc.</span></li>
                            <li class="mb-3"><span class="badge bg-success">SHORTLISTED</span> <span class="text-muted ms-2">Global Systems</span></li>
                            <li><span class="badge bg-warning text-dark">INTERVIEW</span> <span class="text-muted ms-2">Data Corp</span></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(STUDENT_DIR / "dashboard.html", "w", encoding="utf-8") as f: f.write(student_dashboard)


# 3. Officer Analytics Dashboard Template
officer_dashboard = """
{% extends 'base.html' %}
{% block content %}
<div class="container-fluid bg-light min-vh-100 p-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold"><i class="bi bi-speedometer text-primary me-2"></i> CAMPUSLINK COMMAND CENTER</h2>
    </div>
    
    <div class="row g-4 mb-5">
        <div class="col-md-3">
            <div class="card p-4 text-center">
                <h6 class="text-muted fw-bold">Total Students</h6>
                <h2 class="fw-bold text-primary">1,204</h2>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card p-4 text-center">
                <h6 class="text-muted fw-bold">Eligible Students</h6>
                <h2 class="fw-bold text-success">892</h2>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card p-4 text-center">
                <h6 class="text-muted fw-bold">Placement Rate</h6>
                <h2 class="fw-bold text-warning">78%</h2>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card p-4 text-center">
                <h6 class="text-muted fw-bold">Average Package</h6>
                <h2 class="fw-bold text-danger">8.5 LPA</h2>
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-8">
            <div class="card p-4 h-100">
                <h5 class="fw-bold mb-4">Placement by Department</h5>
                <canvas id="placementChart"></canvas>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 h-100 bg-primary text-white">
                <h5 class="fw-bold mb-4"><i class="bi bi-lightbulb me-2"></i> AI Insights</h5>
                <ul class="list-unstyled mt-3">
                    <li class="mb-4"><strong>Insight 1:</strong> Python is the most required skill across 65% of active jobs.</li>
                    <li class="mb-4"><strong>Insight 2:</strong> 120 eligible students have not applied to matching jobs yet.</li>
                    <li><strong>Insight 3:</strong> REST API is missing from 40% of student profiles.</li>
                </ul>
            </div>
        </div>
    </div>
</div>

<script>
    const ctx = document.getElementById('placementChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['CSE', 'IT', 'ECE', 'EEE', 'MECH'],
            datasets: [{
                label: 'Placed Students',
                data: [150, 120, 90, 45, 30],
                backgroundColor: 'rgba(13, 110, 253, 0.5)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1
            }]
        },
        options: { responsive: true }
    });
</script>
{% endblock %}
"""
with open(OFFICER_DIR / "dashboard.html", "w", encoding="utf-8") as f: f.write(officer_dashboard)

print("Phase 3 AI Services and Premium Dashboards generated.")
