import re


SKILL_CATALOG = {
    'Programming': {
        'python': ('Python', 'python'),
        'python3': ('Python', 'python'),
        'java': ('Java', 'java'),
        'javascript': ('JavaScript', 'javascript'),
        'typescript': ('TypeScript', 'typescript'),
        'c++': ('C++', 'c++'),
        'c#': ('C#', 'c#'),
    },
    'Frontend': {
        'react': ('React', 'react'),
        'reactjs': ('React', 'react'),
        'angular': ('Angular', 'angular'),
        'html': ('HTML', 'html'),
        'css': ('CSS', 'css'),
        'bootstrap': ('Bootstrap', 'bootstrap'),
    },
    'Backend': {
        'django': ('Django', 'django'),
        'flask': ('Flask', 'flask'),
        'node.js': ('Node.js', 'node'),
        'nodejs': ('Node.js', 'node'),
        'rest api': ('REST API', 'rest'),
        'rest': ('REST API', 'rest'),
    },
    'Database': {
        'sql': ('SQL', 'sql'),
        'mysql': ('SQL', 'mysql'),
        'postgresql': ('PostgreSQL', 'postgresql'),
        'postgres': ('PostgreSQL', 'postgres'),
        'mongodb': ('MongoDB', 'mongodb'),
    },
    'Cloud': {
        'aws': ('AWS', 'aws'),
        'azure': ('Azure', 'azure'),
        'gcp': ('Google Cloud', 'gcp'),
    },
    'AI/ML': {
        'machine learning': ('Machine Learning', 'machine learning'),
        'deep learning': ('Deep Learning', 'deep learning'),
        'tensorflow': ('TensorFlow', 'tensorflow'),
        'pytorch': ('PyTorch', 'pytorch'),
        'scikit-learn': ('Scikit-learn', 'scikit'),
    },
    'DevOps': {
        'docker': ('Docker', 'docker'),
        'kubernetes': ('Kubernetes', 'kubernetes'),
        'ci/cd': ('CI/CD', 'ci/cd'),
        'git': ('Git', 'git'),
        'github': ('GitHub', 'github'),
    },
    'Tools': {
        'jira': ('Jira', 'jira'),
        'linux': ('Linux', 'linux'),
        'postman': ('Postman', 'postman'),
    },
}


def _contains_skill(text, phrase):
    return re.search(r'(?<![\w+#])' + re.escape(phrase) + r'(?![\w+#])', text, re.IGNORECASE) is not None


def extract_skills(text):
    """Extract normalized skills into stable categories for matching and reporting."""
    lowered = (text or '').lower()
    categorized = {}
    for category, skills in SKILL_CATALOG.items():
        matches = []
        for aliases, (display_name, _) in skills.items():
            if _contains_skill(lowered, aliases) and display_name not in matches:
                matches.append(display_name)
        if matches:
            categorized[category] = sorted(matches)
    return categorized


def normalized_skill_names(text):
    return {
        skill.lower()
        for skills in extract_skills(text).values()
        for skill in skills
    }
