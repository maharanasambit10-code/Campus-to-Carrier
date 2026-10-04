import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
CSS_DIR = STATIC_DIR / "css"
JS_DIR = STATIC_DIR / "js"

for d in [TEMPLATES_DIR, TEMPLATES_DIR/"student", TEMPLATES_DIR/"recruiter", TEMPLATES_DIR/"officer", CSS_DIR, JS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 1. CSS File
css_content = """
:root { --primary-color: #0d6efd; --secondary-color: #6c757d; }
body { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
.card { border: none; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s ease, box-shadow 0.2s ease; }
.card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
.sidebar { background: white; min-height: 100vh; box-shadow: 2px 0 5px rgba(0,0,0,0.05); }
.nav-link { font-weight: 500; padding: 12px 20px; color: var(--secondary-color); border-radius: 8px; margin-bottom: 5px; }
.nav-link:hover, .nav-link.active { background-color: #e9ecef; color: var(--primary-color); }
"""
with open(CSS_DIR / "style.css", "w", encoding="utf-8") as f:
    f.write(css_content)

# 2. JS File
js_content = """
console.log("CAMPUSLINK initialized.");
// Add interactivity logic here for fetch API calls
"""
with open(JS_DIR / "main.js", "w", encoding="utf-8") as f:
    f.write(js_content)

# 3. HTML Files
base_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAMPUSLINK</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/"><i class="bi bi-mortarboard-fill me-2"></i>CAMPUSLINK</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link text-white" href="/">Home</a></li>
                    <li class="nav-item"><a class="btn btn-light ms-2 text-primary fw-bold" href="/login/">Login</a></li>
                </ul>
            </div>
        </div>
    </nav>
    {% block content %}{% endblock %}
    <script src="/static/js/main.js"></script>
</body>
</html>
"""
with open(TEMPLATES_DIR / "base.html", "w", encoding="utf-8") as f:
    f.write(base_html)

home_html = """
{% extends 'base.html' %}
{% block content %}
<div class="container text-center mt-5">
    <h1 class="display-3 fw-bold mb-3 text-primary">From Campus Talent to Corporate Opportunity</h1>
    <p class="lead mb-4">AI-powered career intelligence for students, smarter hiring for recruiters.</p>
</div>
{% endblock %}
"""
with open(TEMPLATES_DIR / "home.html", "w", encoding="utf-8") as f:
    f.write(home_html)

print("HTML, CSS, and JS files have been successfully created directly in the workspace!")
