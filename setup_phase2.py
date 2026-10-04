import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")

# 1. Update settings.py for MySQL and Templates
settings_path = BASE_DIR / "campuslink" / "settings.py"
with open(settings_path, "r") as f:
    settings_content = f.read()

# Add templates dir
if "os.path.join(BASE_DIR, 'templates')" not in settings_content:
    settings_content = settings_content.replace(
        "'DIRS': [],",
        "import os\n        'DIRS': [os.path.join(BASE_DIR, 'templates')],",
        1
    )

# Replace database config
import re
new_db_config = """
import os
from dotenv import load_dotenv
load_dotenv()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if os.getenv('USE_MYSQL') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'campuslink_db'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '3306'),
        }
    }
"""
settings_content = re.sub(
    r"DATABASES = {.*?}\n}", 
    new_db_config, 
    settings_content, 
    flags=re.DOTALL
)

with open(settings_path, "w") as f:
    f.write(settings_content)


# 2. Create .env.example
env_example = """
SECRET_KEY=your_secret_key_here
DEBUG=True
USE_MYSQL=False
DB_NAME=campuslink_db
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
"""
with open(BASE_DIR / ".env.example", "w") as f:
    f.write(env_example.strip())

# 3. Create Admin configurations
admin_code = {
    "accounts": "from django.contrib import admin\nfrom .models import User\nadmin.site.register(User)",
    "students": "from django.contrib import admin\nfrom .models import StudentProfile, Skill, StudentSkill\nadmin.site.register(StudentProfile)\nadmin.site.register(Skill)\nadmin.site.register(StudentSkill)",
    "companies": "from django.contrib import admin\nfrom .models import Company\nadmin.site.register(Company)",
    "recruiters": "from django.contrib import admin\nfrom .models import RecruiterProfile\nadmin.site.register(RecruiterProfile)",
    "jobs": "from django.contrib import admin\nfrom .models import Job\nadmin.site.register(Job)",
    "applications": "from django.contrib import admin\nfrom .models import Application\nadmin.site.register(Application)",
    "ai_engine": "from django.contrib import admin\nfrom .models import ResumeAnalysis, PlacementPrediction\nadmin.site.register(ResumeAnalysis)\nadmin.site.register(PlacementPrediction)",
}

for app, code in admin_code.items():
    with open(BASE_DIR / app / "admin.py", "w") as f:
        f.write(code)

# 4. Generate Templates
templates_dir = BASE_DIR / "templates"
templates_dir.mkdir(exist_ok=True)
(templates_dir / "student").mkdir(exist_ok=True)
(templates_dir / "recruiter").mkdir(exist_ok=True)
(templates_dir / "officer").mkdir(exist_ok=True)

base_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAMPUSLINK - AI Placement Ecosystem</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
        .hero { background: linear-gradient(135deg, #0d6efd, #0dcaf0); color: white; padding: 100px 0; }
        .card { border-radius: 12px; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s; }
        .card:hover { transform: translateY(-5px); }
        .sidebar { background: white; min-height: 100vh; box-shadow: 2px 0 5px rgba(0,0,0,0.05); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/"><i class="bi bi-mortarboard-fill me-2"></i>CAMPUSLINK</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                    <li class="nav-item"><a class="btn btn-light ms-2 text-primary fw-bold" href="#">Login</a></li>
                </ul>
            </div>
        </div>
    </nav>
    {% block content %}{% endblock %}
</body>
</html>
"""
with open(templates_dir / "base.html", "w") as f: f.write(base_html)

home_html = """
{% extends 'base.html' %}
{% block content %}
<div class="hero text-center">
    <div class="container">
        <h1 class="display-3 fw-bold mb-3">From Campus Talent to Corporate Opportunity</h1>
        <p class="lead mb-4">An AI-powered campus-to-corporate placement ecosystem that connects students, institutions and recruiters through intelligent matching, skill analytics and data-driven career insights.</p>
        <button class="btn btn-light btn-lg text-primary fw-bold px-4 rounded-pill shadow">Get Started</button>
        <button class="btn btn-outline-light btn-lg px-4 rounded-pill ms-2">Explore Platform</button>
    </div>
</div>
<div class="container my-5">
    <h2 class="text-center mb-5 fw-bold">AI Features</h2>
    <div class="row g-4">
        <div class="col-md-4">
            <div class="card h-100 p-4 text-center">
                <i class="bi bi-file-earmark-text text-primary fs-1 mb-3"></i>
                <h4 class="fw-bold">Resume Analyzer</h4>
                <p class="text-muted">Extracts skills and gives an ATS score automatically.</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card h-100 p-4 text-center">
                <i class="bi bi-robot text-success fs-1 mb-3"></i>
                <h4 class="fw-bold">AI Job Recommendations</h4>
                <p class="text-muted">Matches student profiles with best jobs using NLP.</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card h-100 p-4 text-center">
                <i class="bi bi-graph-up-arrow text-danger fs-1 mb-3"></i>
                <h4 class="fw-bold">Placement Prediction</h4>
                <p class="text-muted">Predicts readiness score based on academic metrics.</p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(templates_dir / "home.html", "w") as f: f.write(home_html)

print("Phase 2 setup script executed successfully!")
