import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
CSS_DIR = STATIC_DIR / "css"
JS_DIR = STATIC_DIR / "js"

# 1. Advanced CSS
premium_css = """
:root { 
    --primary-color: #4f46e5; 
    --secondary-color: #64748b; 
    --bg-light: #f8fafc;
    --card-bg: #ffffff;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}
body { 
    font-family: 'Inter', sans-serif; 
    background-color: var(--bg-light); 
    color: #334155;
    overflow-x: hidden;
}
/* Smooth Transitions */
.card { 
    border: none; 
    border-radius: 16px; 
    background-color: var(--card-bg);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); 
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
}
.card:hover { 
    transform: translateY(-5px); 
    box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04); 
}
/* Glassmorphism Navbar */
.navbar {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(0,0,0,0.05);
}
.navbar-brand { color: var(--primary-color) !important; font-weight: 800; letter-spacing: -0.5px; }
/* Sidebar styling */
.sidebar { 
    background: white; 
    min-height: calc(100vh - 60px); 
    box-shadow: 2px 0 5px rgba(0,0,0,0.02); 
}
.nav-link { 
    font-weight: 600; 
    padding: 12px 20px; 
    color: var(--secondary-color); 
    border-radius: 12px; 
    margin-bottom: 8px; 
    transition: all 0.2s ease;
}
.nav-link:hover, .nav-link.active { 
    background-color: #e0e7ff; 
    color: var(--primary-color); 
    transform: translateX(5px);
}
/* Badges & Progress */
.badge-soft-success { background-color: #d1fae5; color: #065f46; border: 1px solid #34d399; }
.badge-soft-primary { background-color: #e0e7ff; color: #3730a3; border: 1px solid #818cf8; }
.progress { height: 10px; border-radius: 10px; background-color: #e2e8f0; }
.progress-bar { border-radius: 10px; }

/* Micro Animations */
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.animate-fade-in { animation: fadeIn 0.6s ease forwards; }
"""
with open(CSS_DIR / "style.css", "w", encoding="utf-8") as f:
    f.write(premium_css)

# 2. Interactive JavaScript
premium_js = """
document.addEventListener("DOMContentLoaded", function() {
    console.log("CAMPUSLINK Core loaded.");
    
    // Add staggered fade-in animations to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.classList.add('animate-fade-in');
        card.style.animationDelay = `${index * 0.1}s`;
    });

    // Sidebar Active State Toggle
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.forEach(n => n.classList.remove('active', 'text-primary'));
            this.classList.add('active', 'text-primary');
        });
    });

    // Optional Chart.js Initialization if canvas exists
    const placementCanvas = document.getElementById('placementChart');
    if (placementCanvas) {
        const ctx = placementCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Technical Skills', 'Aptitude', 'Communication', 'Projects'],
                datasets: [{
                    data: [85, 90, 75, 95],
                    backgroundColor: ['#4f46e5', '#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: { cutout: '75%', responsive: true, plugins: { legend: { position: 'bottom' } } }
        });
    }
});
"""
with open(JS_DIR / "main.js", "w", encoding="utf-8") as f:
    f.write(premium_js)

# 3. Premium Base HTML
premium_base = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAMPUSLINK | AI Placement Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container-fluid px-4">
            <a class="navbar-brand d-flex align-items-center" href="/">
                <i class="bi bi-rocket-takeoff-fill me-2 fs-3 text-primary"></i>
                <span>CAMPUSLINK</span>
            </a>
            <div class="d-flex align-items-center gap-3">
                <div class="position-relative">
                    <i class="bi bi-bell fs-5 text-secondary"></i>
                    <span class="position-absolute top-0 start-100 translate-middle p-1 bg-danger border border-light rounded-circle"></span>
                </div>
                <div class="dropdown">
                    <a href="#" class="d-flex align-items-center text-decoration-none dropdown-toggle" data-bs-toggle="dropdown">
                        <img src="https://ui-avatars.com/api/?name=User&background=4f46e5&color=fff" alt="mdo" width="32" height="32" class="rounded-circle me-2">
                        <strong class="text-dark">Demo User</strong>
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end shadow border-0 rounded-3 mt-2">
                        <li><a class="dropdown-item" href="#">Profile</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="/logout/">Sign out</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </nav>
    {% block content %}{% endblock %}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/main.js"></script>
</body>
</html>
"""
with open(TEMPLATES_DIR / "base.html", "w", encoding="utf-8") as f:
    f.write(premium_base)

print("Premium HTML/CSS/JS features applied.")
