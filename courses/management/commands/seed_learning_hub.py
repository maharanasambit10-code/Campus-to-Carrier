"""
Management command: python manage.py seed_learning_hub

Seeds the database with 10 placement-ready courses, lessons, and quizzes.
Safe to run multiple times (uses get_or_create).
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify


COURSES_DATA = [
    {
        "title": "Python Programming",
        "category": "programming",
        "level": "beginner",
        "icon": "bi-filetype-py",
        "icon_color": "#3776AB",
        "icon_bg": "#e8f4fd",
        "duration_hrs": 20,
        "description": (
            "Master Python from scratch — the #1 language for data, AI, and backend development. "
            "This course covers syntax, OOP, file handling, and real-world projects."
        ),
        "objectives": (
            "Understand Python syntax and data types\n"
            "Work with functions, OOP, and modules\n"
            "Build mini-projects: calculator, to-do app, file organizer\n"
            "Handle exceptions and file I/O\n"
            "Prepare for Python-based placement rounds"
        ),
        "lessons": [
            {"title": "Introduction to Python & Setup", "content_type": "text", "duration_min": 15,
             "content_text": "<h4>Welcome to Python!</h4><p>Python is a high-level, interpreted, general-purpose programming language. In this lesson you will install Python and set up VS Code.</p><h5>Steps:</h5><ol><li>Download Python from python.org</li><li>Install VS Code</li><li>Install the Python extension</li><li>Run: <code>print('Hello, World!')</code></li></ol><p>Python is used by companies like Google, Netflix, Instagram, and NASA.</p>"},
            {"title": "Variables, Data Types & Operators", "content_type": "text", "duration_min": 20,
             "content_text": "<h4>Variables & Data Types</h4><p>Python supports: <code>int</code>, <code>float</code>, <code>str</code>, <code>bool</code>, <code>list</code>, <code>tuple</code>, <code>dict</code>, <code>set</code>.</p><pre><code>x = 10\nname = 'Alice'\npi = 3.14\nflags = True\n\n# f-strings\nprint(f'Hello {name}, x={x}')</code></pre>"},
            {"title": "Control Flow: if, for, while", "content_type": "text", "duration_min": 20,
             "content_text": "<h4>Control Flow</h4><pre><code># if-else\nage = 18\nif age >= 18:\n    print('Adult')\nelse:\n    print('Minor')\n\n# for loop\nfor i in range(5):\n    print(i)\n\n# while loop\ncount = 0\nwhile count < 3:\n    count += 1</code></pre>"},
            {"title": "Functions & Recursion", "content_type": "text", "duration_min": 25,
             "content_text": "<h4>Functions</h4><pre><code>def greet(name='World'):\n    return f'Hello, {name}!'\n\n# Recursion\ndef factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)\n\nprint(factorial(5))  # 120</code></pre>"},
            {"title": "Lists, Tuples, Dictionaries & Sets", "content_type": "text", "duration_min": 25,
             "content_text": "<h4>Collections</h4><pre><code>fruits = ['apple', 'banana', 'mango']\ncoords = (10, 20)\nstudent = {'name': 'Rahul', 'cgpa': 8.5}\nunique = {1, 2, 3, 2}  # {1, 2, 3}\n\n# List comprehension\nsquares = [x**2 for x in range(10)]</code></pre>"},
            {"title": "OOP: Classes & Objects", "content_type": "text", "duration_min": 30,
             "content_text": "<h4>Object-Oriented Programming</h4><pre><code>class Animal:\n    def __init__(self, name):\n        self.name = name\n    def speak(self):\n        return f'{self.name} makes a sound'\n\nclass Dog(Animal):\n    def speak(self):\n        return f'{self.name} says Woof!'\n\nd = Dog('Rex')\nprint(d.speak())</code></pre>"},
            {"title": "File Handling & Exception Management", "content_type": "text", "duration_min": 20,
             "content_text": "<h4>File I/O & Exceptions</h4><pre><code># Read file\nwith open('data.txt', 'r') as f:\n    content = f.read()\n\n# Write file\nwith open('output.txt', 'w') as f:\n    f.write('Hello')\n\n# Exception\ntry:\n    result = 10 / 0\nexcept ZeroDivisionError as e:\n    print('Error:', e)\nfinally:\n    print('Done')</code></pre>"},
            {"title": "Mini-Project: Student Grade Calculator", "content_type": "text", "duration_min": 40,
             "content_text": "<h4>Project: Grade Calculator</h4><p>Build a Python CLI app that takes student marks as input, calculates average, and prints the grade (A/B/C/F).</p><pre><code>def calculate_grade(marks):\n    avg = sum(marks) / len(marks)\n    if avg >= 90: return 'A'\n    elif avg >= 75: return 'B'\n    elif avg >= 60: return 'C'\n    else: return 'F'\n\nmarks = [85, 92, 78, 88]\nprint(calculate_grade(marks))</code></pre>"},
        ],
        "quiz": {
            "title": "Python Programming Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "What is the output of print(type(3.14))?", "a": "<class 'float'>", "b": "<class 'int'>", "c": "<class 'double'>", "d": "Error", "ans": "A", "exp": "3.14 is a float literal in Python."},
                {"q": "Which keyword is used to define a function in Python?", "a": "function", "b": "def", "c": "func", "d": "define", "ans": "B", "exp": "Python uses 'def' to declare functions."},
                {"q": "What does len([1,2,3]) return?", "a": "2", "b": "3", "c": "4", "d": "Error", "ans": "B", "exp": "len() counts elements; the list has 3 elements."},
                {"q": "Which is immutable in Python?", "a": "List", "b": "Dictionary", "c": "Tuple", "d": "Set", "ans": "C", "exp": "Tuples cannot be modified after creation."},
                {"q": "What is the result of 10 // 3?", "a": "3.33", "b": "3", "c": "4", "d": "1", "ans": "B", "exp": "// is floor division, returning integer quotient."},
            ],
        },
    },
    {
        "title": "Java Programming",
        "category": "programming",
        "level": "intermediate",
        "icon": "bi-cup-hot-fill",
        "icon_color": "#f89820",
        "icon_bg": "#fff8e1",
        "duration_hrs": 25,
        "description": "Learn Java, the cornerstone of enterprise development and Android apps. Covers OOP, collections, multithreading, and interview coding patterns.",
        "objectives": (
            "Understand Java syntax and JVM internals\n"
            "Master OOP: inheritance, polymorphism, abstraction\n"
            "Work with Java Collections Framework\n"
            "Handle exceptions and multithreading basics\n"
            "Solve placement coding questions in Java"
        ),
        "lessons": [
            {"title": "Java Setup, JDK & Hello World", "content_type": "text", "duration_min": 15, "content_text": "<h4>Getting Started with Java</h4><p>Download JDK 17+ from oracle.com. Compile: <code>javac Hello.java</code>, Run: <code>java Hello</code>.</p><pre><code>public class Hello {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}</code></pre>"},
            {"title": "Data Types, Variables & Operators", "content_type": "text", "duration_min": 20, "content_text": "<h4>Java Data Types</h4><pre><code>int age = 20;\ndouble gpa = 8.5;\nString name = \"Rahul\";\nboolean isStudent = true;\nchar grade = 'A';</code></pre>"},
            {"title": "OOP: Classes, Inheritance & Interfaces", "content_type": "text", "duration_min": 35, "content_text": "<h4>OOP in Java</h4><pre><code>class Animal {\n    String name;\n    void speak() { System.out.println(name + \" speaks\"); }\n}\nclass Dog extends Animal {\n    void speak() { System.out.println(name + \" barks\"); }\n}\n\ninterface Runnable {\n    void run();\n}</code></pre>"},
            {"title": "Collections: ArrayList, HashMap, HashSet", "content_type": "text", "duration_min": 25, "content_text": "<h4>Java Collections</h4><pre><code>import java.util.*;\nArrayList<String> list = new ArrayList<>();\nlist.add(\"Alice\");\n\nHashMap<String, Integer> map = new HashMap<>();\nmap.put(\"score\", 95);</code></pre>"},
            {"title": "Exception Handling & File I/O", "content_type": "text", "duration_min": 20, "content_text": "<h4>Exceptions in Java</h4><pre><code>try {\n    int result = 10 / 0;\n} catch (ArithmeticException e) {\n    System.out.println(\"Error: \" + e.getMessage());\n} finally {\n    System.out.println(\"Done\");\n}</code></pre>"},
            {"title": "Coding Interview Patterns in Java", "content_type": "text", "duration_min": 45, "content_text": "<h4>Common Patterns</h4><p>Two-pointer, sliding window, recursion, binary search — all essential for placement rounds.</p><pre><code>// Reverse a string\nString reversed = new StringBuilder(str).reverse().toString();\n\n// Check palindrome\nboolean isPalin = str.equals(reversed);</code></pre>"},
        ],
        "quiz": {
            "title": "Java Programming Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "Which access modifier makes a member accessible only within the same class?", "a": "public", "b": "protected", "c": "private", "d": "default", "ans": "C", "exp": "private restricts access to the declaring class only."},
                {"q": "What is the parent class of all Java classes?", "a": "Base", "b": "Super", "c": "Object", "d": "Root", "ans": "C", "exp": "java.lang.Object is the root of the Java class hierarchy."},
                {"q": "Which keyword prevents method overriding?", "a": "static", "b": "final", "c": "abstract", "d": "sealed", "ans": "B", "exp": "final methods cannot be overridden in subclasses."},
                {"q": "ArrayList is part of which package?", "a": "java.io", "b": "java.lang", "c": "java.util", "d": "java.net", "ans": "C", "exp": "Collections like ArrayList reside in java.util."},
                {"q": "What does JVM stand for?", "a": "Java Virtual Machine", "b": "Java Visual Module", "c": "Java Version Manager", "d": "Java Verified Method", "ans": "A", "exp": "JVM executes Java bytecode on any platform."},
            ],
        },
    },
    {
        "title": "C and C++",
        "category": "programming",
        "level": "beginner",
        "icon": "bi-cpu",
        "icon_color": "#00599C",
        "icon_bg": "#e3f2fd",
        "duration_hrs": 18,
        "description": "Build a rock-solid programming foundation with C and C++. Essential for competitive programming, system design, and core CS placements.",
        "objectives": (
            "Understand pointers and memory management in C\n"
            "Work with arrays, strings, and structs\n"
            "Learn C++ OOP and STL\n"
            "Solve problems using arrays and recursion\n"
            "Master common data structure implementations"
        ),
        "lessons": [
            {"title": "C Basics: Hello World, Variables, I/O", "content_type": "text", "duration_min": 15, "content_text": "<pre><code>#include &lt;stdio.h&gt;\nint main() {\n    int x = 10;\n    printf(\"x = %d\\n\", x);\n    return 0;\n}</code></pre>"},
            {"title": "Pointers & Memory in C", "content_type": "text", "duration_min": 30, "content_text": "<h4>Pointers</h4><pre><code>int a = 5;\nint *p = &a;\nprintf(\"%d\", *p);  // 5\n*p = 20;\nprintf(\"%d\", a);   // 20</code></pre>"},
            {"title": "Arrays, Strings & Structs", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>int arr[5] = {1,2,3,4,5};\nchar name[] = \"Rahul\";\n\nstruct Student {\n    char name[50];\n    float cgpa;\n};</code></pre>"},
            {"title": "C++ OOP: Classes & Inheritance", "content_type": "text", "duration_min": 30, "content_text": "<pre><code>class Shape {\npublic:\n    virtual double area() = 0;\n};\nclass Circle : public Shape {\n    double r;\npublic:\n    Circle(double r): r(r) {}\n    double area() { return 3.14 * r * r; }\n};</code></pre>"},
            {"title": "STL: vectors, maps, sets, algorithms", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>#include &lt;vector&gt;\n#include &lt;algorithm&gt;\nvector&lt;int&gt; v = {3,1,4,1,5};\nsort(v.begin(), v.end());\n// v = {1,1,3,4,5}</code></pre>"},
        ],
        "quiz": {
            "title": "C & C++ Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "What does the & operator do in C?", "a": "Bitwise AND", "b": "Address of", "c": "Logical AND", "d": "None", "ans": "B", "exp": "&variable gives the memory address of the variable."},
                {"q": "Which header provides printf in C?", "a": "stdlib.h", "b": "string.h", "c": "stdio.h", "d": "math.h", "ans": "C", "exp": "stdio.h (Standard Input/Output) provides printf and scanf."},
                {"q": "What is the size of int typically on a 64-bit system?", "a": "2 bytes", "b": "4 bytes", "c": "8 bytes", "d": "Depends on compiler", "ans": "B", "exp": "int is typically 4 bytes on most 64-bit systems."},
                {"q": "Which C++ feature supports compile-time polymorphism?", "a": "Virtual functions", "b": "Templates", "c": "Inheritance", "d": "Constructors", "ans": "B", "exp": "Templates enable generic programming and compile-time polymorphism."},
                {"q": "STL stands for?", "a": "Standard Template Library", "b": "Static Type Library", "c": "Simple Type Language", "d": "Structured Type List", "ans": "A", "exp": "STL = Standard Template Library, part of C++ standard library."},
            ],
        },
    },
    {
        "title": "HTML, CSS & JavaScript",
        "category": "web",
        "level": "beginner",
        "icon": "bi-code-slash",
        "icon_color": "#e34c26",
        "icon_bg": "#fce8e3",
        "duration_hrs": 22,
        "description": "Learn the three pillars of the web. Build beautiful, interactive pages from scratch using modern HTML5, CSS3, and vanilla JavaScript.",
        "objectives": (
            "Build semantic HTML5 pages\n"
            "Style with CSS3: flexbox, grid, animations\n"
            "Add interactivity with JavaScript DOM manipulation\n"
            "Work with forms, events, and local storage\n"
            "Build 3 responsive mini-projects"
        ),
        "lessons": [
            {"title": "HTML5 Structure & Semantic Elements", "content_type": "text", "duration_min": 20, "content_text": "<pre><code>&lt;!DOCTYPE html&gt;\n&lt;html lang=\"en\"&gt;\n&lt;head&gt;&lt;title&gt;My Page&lt;/title&gt;&lt;/head&gt;\n&lt;body&gt;\n  &lt;header&gt;&lt;h1&gt;Welcome&lt;/h1&gt;&lt;/header&gt;\n  &lt;main&gt;&lt;p&gt;Content here&lt;/p&gt;&lt;/main&gt;\n  &lt;footer&gt;© 2026&lt;/footer&gt;\n&lt;/body&gt;&lt;/html&gt;</code></pre>"},
            {"title": "CSS: Selectors, Box Model & Flexbox", "content_type": "text", "duration_min": 30, "content_text": "<pre><code>.card {\n  display: flex;\n  gap: 1rem;\n  padding: 1rem;\n  border-radius: 8px;\n  box-shadow: 0 2px 8px rgba(0,0,0,0.1);\n}\n.card:hover { transform: translateY(-4px); }</code></pre>"},
            {"title": "CSS Grid & Responsive Design", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>.grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));\n  gap: 1.5rem;\n}\n@media (max-width: 600px) {\n  .grid { grid-template-columns: 1fr; }\n}</code></pre>"},
            {"title": "JavaScript: Variables, Functions & DOM", "content_type": "text", "duration_min": 30, "content_text": "<pre><code>const btn = document.getElementById('myBtn');\nbtn.addEventListener('click', () => {\n  document.querySelector('h1').textContent = 'Clicked!';\n});\n\n// Arrow function\nconst greet = name => `Hello, ${name}!`;</code></pre>"},
            {"title": "JS: Events, Forms & Local Storage", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>// Save to localStorage\nlocalStorage.setItem('user', JSON.stringify({name:'Rahul'}));\n// Read\nconst user = JSON.parse(localStorage.getItem('user'));\n\n// Form validation\nform.addEventListener('submit', e => {\n  if (!email.value) e.preventDefault();\n});</code></pre>"},
            {"title": "Project: Responsive Portfolio Page", "content_type": "text", "duration_min": 60, "content_text": "<h4>Build Your Portfolio</h4><p>Using everything you have learned, build a responsive single-page portfolio with: navbar, hero section, skills section, projects grid, and contact form.</p>"},
        ],
        "quiz": {
            "title": "HTML, CSS & JS Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "Which HTML tag is used for the largest heading?", "a": "h6", "b": "h1", "c": "head", "d": "title", "ans": "B", "exp": "h1 is the largest and most important heading tag."},
                {"q": "CSS property to make elements in a row?", "a": "display: block", "b": "display: inline-block", "c": "display: flex", "d": "position: relative", "ans": "C", "exp": "display:flex turns an element into a flex container."},
                {"q": "What does DOM stand for?", "a": "Data Object Model", "b": "Document Object Model", "c": "Dynamic Object Module", "d": "Design Output Module", "ans": "B", "exp": "DOM = Document Object Model, the tree structure of an HTML page."},
                {"q": "Which JS method selects an element by ID?", "a": "querySelector", "b": "getElementsByClass", "c": "getElementById", "d": "getElement", "ans": "C", "exp": "document.getElementById('id') returns the element with that ID."},
                {"q": "How do you add an event listener in JavaScript?", "a": "element.on('click', fn)", "b": "element.click = fn", "c": "element.addEventListener('click', fn)", "d": "element.addEvent('click', fn)", "ans": "C", "exp": "addEventListener is the standard way to attach event handlers."},
            ],
        },
    },
    {
        "title": "Django Web Development",
        "category": "web",
        "level": "intermediate",
        "icon": "bi-server",
        "icon_color": "#092e20",
        "icon_bg": "#e8f5e9",
        "duration_hrs": 30,
        "description": "Build full-stack web applications with Django. Learn models, views, templates, forms, authentication, and REST APIs — everything you need for a backend developer role.",
        "objectives": (
            "Understand the Django MVT architecture\n"
            "Build models and run migrations\n"
            "Create views and templates with DTL\n"
            "Implement user authentication and permissions\n"
            "Build a CRUD web application end-to-end"
        ),
        "lessons": [
            {"title": "Django Project Setup & MVT Architecture", "content_type": "text", "duration_min": 20, "content_text": "<pre><code>pip install django\ndjango-admin startproject myproject\ncd myproject\npython manage.py startapp blog\npython manage.py runserver</code></pre>"},
            {"title": "Models & Database Migrations", "content_type": "text", "duration_min": 30, "content_text": "<pre><code>from django.db import models\n\nclass Post(models.Model):\n    title   = models.CharField(max_length=200)\n    content = models.TextField()\n    created = models.DateTimeField(auto_now_add=True)\n\n    def __str__(self):\n        return self.title</code></pre><p>Run: <code>python manage.py makemigrations && python manage.py migrate</code></p>"},
            {"title": "Views, URLs & Templates", "content_type": "text", "duration_min": 30, "content_text": "<pre><code># views.py\nfrom django.shortcuts import render\nfrom .models import Post\n\ndef post_list(request):\n    posts = Post.objects.all()\n    return render(request, 'blog/list.html', {'posts': posts})</code></pre>"},
            {"title": "Forms, Validation & CSRF", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>from django import forms\n\nclass PostForm(forms.ModelForm):\n    class Meta:\n        model = Post\n        fields = ['title', 'content']</code></pre>"},
            {"title": "User Authentication (Login/Register/Logout)", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>from django.contrib.auth import authenticate, login\n\ndef login_view(request):\n    if request.method == 'POST':\n        user = authenticate(username=..., password=...)\n        if user:\n            login(request, user)\n            return redirect('home')</code></pre>"},
            {"title": "Class-Based Views & Django Admin", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>from django.views.generic import ListView\n\nclass PostListView(ListView):\n    model = Post\n    template_name = 'blog/list.html'\n    context_object_name = 'posts'</code></pre>"},
            {"title": "Project: Build a Job Board", "content_type": "text", "duration_min": 90, "content_text": "<h4>Capstone: Job Board</h4><p>Build a Django job board where companies can post jobs and students can apply. Include authentication, admin panel, and job filtering.</p>"},
        ],
        "quiz": {
            "title": "Django Web Development Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "What does MVT stand for in Django?", "a": "Model View Template", "b": "Module View Type", "c": "Main View Table", "d": "Module Visual Tool", "ans": "A", "exp": "Django uses Model-View-Template architecture (similar to MVC)."},
                {"q": "Which command creates database tables from models?", "a": "python manage.py createdb", "b": "python manage.py syncdb", "c": "python manage.py migrate", "d": "python manage.py setup", "ans": "C", "exp": "migrate applies migrations to create/modify database tables."},
                {"q": "What does @login_required decorator do?", "a": "Logs in the user automatically", "b": "Redirects unauthenticated users to login page", "c": "Creates a login page", "d": "Validates the user's password", "ans": "B", "exp": "@login_required redirects to LOGIN_URL if user is not authenticated."},
                {"q": "Which file contains URL patterns in a Django app?", "a": "models.py", "b": "urls.py", "c": "views.py", "d": "settings.py", "ans": "B", "exp": "urls.py holds the URL routing patterns for each app."},
                {"q": "What is 'render' in Django views?", "a": "A database query method", "b": "A shortcut to return an HttpResponse with a rendered template", "c": "A URL resolver", "d": "A form validation method", "ans": "B", "exp": "render(request, template, context) is a shortcut for rendering templates."},
            ],
        },
    },
    {
        "title": "SQL & MySQL Database",
        "category": "database",
        "level": "beginner",
        "icon": "bi-database",
        "icon_color": "#4479A1",
        "icon_bg": "#e8f0fd",
        "duration_hrs": 15,
        "description": "Master SQL and MySQL — from basic queries to joins, indexes, stored procedures, and database design. A must-have skill for every developer.",
        "objectives": (
            "Write SELECT, INSERT, UPDATE, DELETE queries\n"
            "Use JOINs: INNER, LEFT, RIGHT, FULL\n"
            "Design normalized databases with ER diagrams\n"
            "Use GROUP BY, HAVING, subqueries, and CTEs\n"
            "Understand indexes, transactions, and stored procedures"
        ),
        "lessons": [
            {"title": "Database Concepts & MySQL Setup", "content_type": "text", "duration_min": 15, "content_text": "<h4>Relational Databases</h4><p>A database is an organized collection of structured data. MySQL is an open-source RDBMS. Install MySQL Workbench or use phpMyAdmin.</p><pre><code>CREATE DATABASE campus;\nUSE campus;\nSHOW TABLES;</code></pre>"},
            {"title": "DDL: CREATE, ALTER, DROP Tables", "content_type": "text", "duration_min": 20, "content_text": "<pre><code>CREATE TABLE students (\n  id   INT PRIMARY KEY AUTO_INCREMENT,\n  name VARCHAR(100) NOT NULL,\n  cgpa DECIMAL(3,2),\n  dept VARCHAR(50)\n);\n\nALTER TABLE students ADD email VARCHAR(150);</code></pre>"},
            {"title": "DML: SELECT, INSERT, UPDATE, DELETE", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>-- Insert\nINSERT INTO students (name, cgpa) VALUES ('Rahul', 8.5);\n\n-- Select with WHERE\nSELECT * FROM students WHERE cgpa > 8.0 ORDER BY cgpa DESC;\n\n-- Update\nUPDATE students SET cgpa = 9.0 WHERE id = 1;\n\n-- Delete\nDELETE FROM students WHERE id = 5;</code></pre>"},
            {"title": "JOINs: INNER, LEFT, RIGHT", "content_type": "text", "duration_min": 30, "content_text": "<pre><code>-- INNER JOIN\nSELECT s.name, j.title\nFROM students s\nINNER JOIN applications a ON s.id = a.student_id\nINNER JOIN jobs j ON a.job_id = j.id;\n\n-- LEFT JOIN (all students, even without applications)\nSELECT s.name, a.status\nFROM students s\nLEFT JOIN applications a ON s.id = a.student_id;</code></pre>"},
            {"title": "GROUP BY, HAVING, Aggregate Functions", "content_type": "text", "duration_min": 20, "content_text": "<pre><code>-- Count students per department\nSELECT dept, COUNT(*) as total, AVG(cgpa) as avg_cgpa\nFROM students\nGROUP BY dept\nHAVING COUNT(*) > 5\nORDER BY avg_cgpa DESC;</code></pre>"},
            {"title": "Subqueries, Views & Indexes", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>-- Subquery\nSELECT name FROM students\nWHERE cgpa > (SELECT AVG(cgpa) FROM students);\n\n-- Create View\nCREATE VIEW top_students AS\nSELECT name, cgpa FROM students WHERE cgpa >= 9;\n\n-- Index for performance\nCREATE INDEX idx_dept ON students(dept);</code></pre>"},
        ],
        "quiz": {
            "title": "SQL & MySQL Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "Which SQL clause filters records after GROUP BY?", "a": "WHERE", "b": "FILTER", "c": "HAVING", "d": "ORDER BY", "ans": "C", "exp": "HAVING filters groups; WHERE filters rows before grouping."},
                {"q": "What does PRIMARY KEY ensure?", "a": "Unique and not null values", "b": "Only unique values", "c": "Only not null values", "d": "Foreign key reference", "ans": "A", "exp": "PRIMARY KEY enforces both uniqueness and NOT NULL constraints."},
                {"q": "Which JOIN returns all rows from the left table?", "a": "INNER JOIN", "b": "RIGHT JOIN", "c": "LEFT JOIN", "d": "FULL JOIN", "ans": "C", "exp": "LEFT JOIN returns all left table rows, matched or not."},
                {"q": "What is the purpose of an index in SQL?", "a": "To sort data", "b": "To speed up query performance", "c": "To enforce constraints", "d": "To create backups", "ans": "B", "exp": "Indexes allow the database engine to find rows faster."},
                {"q": "Which aggregate function returns the number of rows?", "a": "SUM()", "b": "AVG()", "c": "MAX()", "d": "COUNT()", "ans": "D", "exp": "COUNT(*) counts all rows; COUNT(col) counts non-null values."},
            ],
        },
    },
    {
        "title": "Data Structures & Algorithms",
        "category": "programming",
        "level": "intermediate",
        "icon": "bi-diagram-3",
        "icon_color": "#7c3aed",
        "icon_bg": "#ede9fe",
        "duration_hrs": 35,
        "description": "The backbone of every placement round. Master arrays, linked lists, stacks, queues, trees, graphs, sorting, and dynamic programming.",
        "objectives": (
            "Implement and analyze fundamental data structures\n"
            "Solve array and string problems efficiently\n"
            "Master recursion, backtracking, and DP\n"
            "Understand graph traversal: BFS and DFS\n"
            "Crack placement and FAANG coding rounds"
        ),
        "lessons": [
            {"title": "Arrays & Time Complexity Analysis", "content_type": "text", "duration_min": 30, "content_text": "<h4>Arrays & Big-O</h4><p>Big-O notation describes algorithm efficiency. O(1) < O(log n) < O(n) < O(n log n) < O(n²).</p><pre><code># Two Sum (O(n) with hash map)\ndef two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target-n], i]\n        seen[n] = i</code></pre>"},
            {"title": "Linked Lists: Singly & Doubly", "content_type": "text", "duration_min": 30, "content_text": "<pre><code>class Node:\n    def __init__(self, val):\n        self.val = val\n        self.next = None\n\nclass LinkedList:\n    def __init__(self): self.head = None\n    def append(self, val):\n        if not self.head: self.head = Node(val)\n        else:\n            cur = self.head\n            while cur.next: cur = cur.next\n            cur.next = Node(val)</code></pre>"},
            {"title": "Stacks & Queues", "content_type": "text", "duration_min": 25, "content_text": "<pre><code>from collections import deque\n# Stack\nstack = []\nstack.append(1)\nstack.pop()\n\n# Queue\nqueue = deque()\nqueue.append(1)\nqueue.popleft()</code></pre>"},
            {"title": "Binary Trees & BST", "content_type": "text", "duration_min": 35, "content_text": "<pre><code>class TreeNode:\n    def __init__(self, val):\n        self.val = val\n        self.left = self.right = None\n\ndef inorder(node):\n    if node:\n        inorder(node.left)\n        print(node.val)\n        inorder(node.right)</code></pre>"},
            {"title": "Sorting Algorithms (Merge, Quick, Heap)", "content_type": "text", "duration_min": 35, "content_text": "<pre><code>def merge_sort(arr):\n    if len(arr) <= 1: return arr\n    mid = len(arr) // 2\n    left  = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(l, r):\n    result = []\n    i = j = 0\n    while i < len(l) and j < len(r):\n        if l[i] <= r[j]: result.append(l[i]); i+=1\n        else:            result.append(r[j]); j+=1\n    return result + l[i:] + r[j:]</code></pre>"},
            {"title": "Dynamic Programming: Memoization & Tabulation", "content_type": "text", "duration_min": 45, "content_text": "<pre><code># Fibonacci with memoization\nfrom functools import lru_cache\n@lru_cache(maxsize=None)\ndef fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)\n\n# 0/1 Knapsack (tabulation)\ndef knapsack(weights, values, capacity):\n    n = len(weights)\n    dp = [[0]*(capacity+1) for _ in range(n+1)]\n    for i in range(1, n+1):\n        for w in range(capacity+1):\n            dp[i][w] = dp[i-1][w]\n            if weights[i-1] <= w:\n                dp[i][w] = max(dp[i][w], dp[i-1][w-weights[i-1]] + values[i-1])\n    return dp[n][capacity]</code></pre>"},
            {"title": "Graphs: BFS, DFS & Shortest Path", "content_type": "text", "duration_min": 40, "content_text": "<pre><code>from collections import deque\n\ndef bfs(graph, start):\n    visited = set()\n    queue = deque([start])\n    while queue:\n        node = queue.popleft()\n        if node not in visited:\n            visited.add(node)\n            queue.extend(graph.get(node, []))\n    return visited</code></pre>"},
        ],
        "quiz": {
            "title": "DSA Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "Time complexity of binary search?", "a": "O(n)", "b": "O(n²)", "c": "O(log n)", "d": "O(n log n)", "ans": "C", "exp": "Binary search halves the search space each step → O(log n)."},
                {"q": "Which data structure uses LIFO order?", "a": "Queue", "b": "Stack", "c": "Linked List", "d": "Tree", "ans": "B", "exp": "Stack = Last In, First Out (push/pop from top)."},
                {"q": "What is the height of a balanced BST with n nodes?", "a": "O(n)", "b": "O(log n)", "c": "O(n²)", "d": "O(1)", "ans": "B", "exp": "A balanced BST has height O(log n)."},
                {"q": "BFS uses which data structure internally?", "a": "Stack", "b": "Priority Queue", "c": "Queue", "d": "Array", "ans": "C", "exp": "BFS explores level-by-level using a Queue (FIFO)."},
                {"q": "Which sorting algorithm has O(n log n) average case?", "a": "Bubble Sort", "b": "Selection Sort", "c": "Merge Sort", "d": "Insertion Sort", "ans": "C", "exp": "Merge Sort always runs in O(n log n) time."},
            ],
        },
    },
    {
        "title": "Aptitude & Reasoning",
        "category": "aptitude",
        "level": "beginner",
        "icon": "bi-calculator",
        "icon_color": "#d97706",
        "icon_bg": "#fef3c7",
        "duration_hrs": 12,
        "description": "Sharpen your quantitative aptitude and logical reasoning skills for placement written tests. Covers number systems, percentages, time-work, puzzles, and more.",
        "objectives": (
            "Solve number system and arithmetic problems quickly\n"
            "Master percentages, profit-loss, time-speed-distance\n"
            "Crack logical reasoning and seating arrangement\n"
            "Improve mental math with shortcut techniques\n"
            "Score high in placement aptitude rounds"
        ),
        "lessons": [
            {"title": "Number Systems & Divisibility Rules", "content_type": "text", "duration_min": 20, "content_text": "<h4>Divisibility Rules</h4><ul><li>÷2: even last digit</li><li>÷3: sum of digits divisible by 3</li><li>÷5: ends in 0 or 5</li><li>÷11: alternating sum divisible by 11</li></ul><p>LCM × HCF = Product of two numbers.</p>"},
            {"title": "Percentages, Profit & Loss", "content_type": "text", "duration_min": 20, "content_text": "<p>Profit% = (Profit / CP) × 100<br>Loss% = (Loss / CP) × 100</p><p>Shortcut: 20% of 350 → 10% = 35, 20% = 70</p>"},
            {"title": "Time, Speed & Distance", "content_type": "text", "duration_min": 20, "content_text": "<p>Speed = Distance / Time<br>Relative speed (same direction) = |s1 - s2|<br>Relative speed (opposite) = s1 + s2</p><p>Tip: Convert km/hr to m/s → multiply by 5/18</p>"},
            {"title": "Time & Work", "content_type": "text", "duration_min": 20, "content_text": "<p>If A does work in 'a' days, rate = 1/a per day.<br>Combined rate = 1/a + 1/b.<br>Time = 1 / (combined rate).</p>"},
            {"title": "Logical Reasoning: Puzzles & Seating", "content_type": "text", "duration_min": 25, "content_text": "<h4>Approach to Puzzles</h4><ol><li>Read all clues</li><li>Draw a table/matrix</li><li>Fill definite information first</li><li>Use elimination for remaining cells</li></ol>"},
            {"title": "Permutations, Combinations & Probability", "content_type": "text", "duration_min": 25, "content_text": "<p>nPr = n! / (n-r)! — Ordered arrangements<br>nCr = n! / (r! × (n-r)!) — Unordered selections</p><p>P(event) = Favourable / Total outcomes</p>"},
        ],
        "quiz": {
            "title": "Aptitude Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "If A can do a work in 10 days and B in 15 days, how many days to do it together?", "a": "5", "b": "6", "c": "8", "d": "25", "ans": "B", "exp": "1/10 + 1/15 = 1/6 → 6 days together."},
                {"q": "What is 15% of 240?", "a": "30", "b": "32", "c": "36", "d": "40", "ans": "C", "exp": "15% of 240 = 0.15 × 240 = 36."},
                {"q": "A train 180m long passes a pole in 9s. Its speed is?", "a": "15 m/s", "b": "18 m/s", "c": "20 m/s", "d": "25 m/s", "ans": "C", "exp": "Speed = 180/9 = 20 m/s."},
                {"q": "How many ways can 4 people sit in a row?", "a": "12", "b": "16", "c": "24", "d": "256", "ans": "C", "exp": "4! = 4×3×2×1 = 24 arrangements."},
                {"q": "If SP = ₹800, Profit = 25%, then CP = ?", "a": "₹600", "b": "₹640", "c": "₹660", "d": "₹700", "ans": "B", "exp": "CP = SP / (1 + profit%) = 800 / 1.25 = 640."},
            ],
        },
    },
    {
        "title": "Communication Skills",
        "category": "communication",
        "level": "beginner",
        "icon": "bi-chat-quote",
        "icon_color": "#0891b2",
        "icon_bg": "#e0f7fa",
        "duration_hrs": 10,
        "description": "Master professional communication — verbal, written, and non-verbal. Ace group discussions, HR interviews, email writing, and workplace conversations.",
        "objectives": (
            "Communicate confidently in English\n"
            "Structure professional emails and reports\n"
            "Perform well in Group Discussion rounds\n"
            "Give impactful self-introductions\n"
            "Handle difficult workplace conversations"
        ),
        "lessons": [
            {"title": "The 7 Cs of Communication", "content_type": "text", "duration_min": 15, "content_text": "<h4>The 7 Cs</h4><ol><li><strong>Clear</strong> — Easy to understand</li><li><strong>Concise</strong> — No unnecessary words</li><li><strong>Correct</strong> — No errors</li><li><strong>Complete</strong> — All info included</li><li><strong>Courteous</strong> — Respectful tone</li><li><strong>Considerate</strong> — Audience-focused</li><li><strong>Concrete</strong> — Specific facts</li></ol>"},
            {"title": "Professional Email Writing", "content_type": "text", "duration_min": 20, "content_text": "<h4>Email Structure</h4><p><strong>Subject:</strong> Job Application — Software Engineer — Rahul Kumar</p><p><strong>Body:</strong></p><ul><li>Opening: Dear [Name],</li><li>Purpose: I am writing to apply for...</li><li>Value: I bring [specific skills]...</li><li>CTA: I would welcome a conversation...</li><li>Closing: Thank you for your time. Warm regards,</li></ul>"},
            {"title": "Confident Self-Introduction (Tell Me About Yourself)", "content_type": "text", "duration_min": 20, "content_text": "<h4>The PAST-PRESENT-FUTURE Formula</h4><ul><li><strong>Past:</strong> Background and education</li><li><strong>Present:</strong> Current skills and projects</li><li><strong>Future:</strong> Career goals and why this role</li></ul><p>Keep it under 2 minutes. Practice 5 times daily.</p>"},
            {"title": "Group Discussion Strategies", "content_type": "text", "duration_min": 20, "content_text": "<h4>GD Tips</h4><ol><li>Initiate if you have a good point — score big</li><li>Use structured speech: Point → Example → Impact</li><li>Listen actively, don't interrupt rudely</li><li>Summarize at the end to stand out</li><li>Avoid filler words: um, like, you know</li></ol>"},
            {"title": "Body Language & Non-Verbal Communication", "content_type": "text", "duration_min": 15, "content_text": "<h4>Non-Verbal Cues</h4><ul><li>Maintain eye contact (not staring)</li><li>Firm handshake, upright posture</li><li>No crossed arms (defensive signal)</li><li>Smile genuinely — builds rapport</li><li>Speak at moderate pace, vary tone</li></ul>"},
        ],
        "quiz": {
            "title": "Communication Skills Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "Which is NOT one of the 7 Cs of Communication?", "a": "Clear", "b": "Concise", "c": "Creative", "d": "Correct", "ans": "C", "exp": "Creative is not part of the 7 Cs. The 7 Cs are: Clear, Concise, Correct, Complete, Courteous, Considerate, Concrete."},
                {"q": "What is the ideal length for a self-introduction in an HR interview?", "a": "30 seconds", "b": "1-2 minutes", "c": "5 minutes", "d": "10 minutes", "ans": "B", "exp": "A 1-2 minute self-intro is perfect — long enough to cover key points, short enough to maintain attention."},
                {"q": "In a Group Discussion, what scores the most points?", "a": "Speaking the most", "b": "Agreeing with everyone", "c": "Initiating with a relevant point", "d": "Staying silent", "ans": "C", "exp": "Initiating a GD with a clear, relevant point signals leadership and confidence."},
                {"q": "Which body language shows confidence?", "a": "Crossed arms", "b": "Looking down", "c": "Upright posture and eye contact", "d": "Leaning back with feet on table", "ans": "C", "exp": "Upright posture and steady eye contact project confidence and engagement."},
                {"q": "What makes an email subject line effective?", "a": "All caps for urgency", "b": "Vague and mysterious", "c": "Specific, clear and relevant", "d": "Very long for detail", "ans": "C", "exp": "Effective subject lines are specific, clear, and tell the reader exactly what to expect."},
            ],
        },
    },
    {
        "title": "Interview Preparation",
        "category": "interview",
        "level": "intermediate",
        "icon": "bi-person-badge",
        "icon_color": "#be185d",
        "icon_bg": "#fce7f3",
        "duration_hrs": 15,
        "description": "Comprehensive placement interview preparation — technical, HR, and behavioral rounds. Includes resume tips, common questions, STAR method, and salary negotiation.",
        "objectives": (
            "Answer HR and behavioral questions confidently\n"
            "Use the STAR method for situational questions\n"
            "Prepare for technical screening rounds\n"
            "Negotiate salary professionally\n"
            "Avoid common interview mistakes"
        ),
        "lessons": [
            {"title": "Types of Interviews: HR, Technical, Case", "content_type": "text", "duration_min": 15, "content_text": "<h4>Interview Types</h4><ul><li><strong>HR Round:</strong> Personality, culture fit, motivation</li><li><strong>Technical Round:</strong> Coding, system design, domain knowledge</li><li><strong>Managerial Round:</strong> Leadership, teamwork, past projects</li><li><strong>Case Interview:</strong> Problem-solving, business acumen (for consulting)</li></ul>"},
            {"title": "Top 10 HR Questions & Answers", "content_type": "text", "duration_min": 30, "content_text": "<h4>Key HR Questions</h4><ol><li>Tell me about yourself → PAST-PRESENT-FUTURE</li><li>Why this company? → Research + Alignment</li><li>Strengths & Weaknesses → Honest + Growth mindset</li><li>Where do you see yourself in 5 years? → Ambitious but realistic</li><li>Why should we hire you? → Specific value you bring</li></ol>"},
            {"title": "STAR Method for Behavioral Questions", "content_type": "text", "duration_min": 25, "content_text": "<h4>STAR = Situation, Task, Action, Result</h4><p>Example: 'Tell me about a time you led a project.'</p><ul><li><strong>S:</strong> Our team needed to build a web app in 2 weeks</li><li><strong>T:</strong> I was assigned as project lead</li><li><strong>A:</strong> I created a sprint plan, assigned tasks daily</li><li><strong>R:</strong> Delivered on time, professor gave A grade</li></ul>"},
            {"title": "Technical Interview: Coding & System Design Basics", "content_type": "text", "duration_min": 30, "content_text": "<h4>Coding Interview Tips</h4><ol><li>Clarify the problem before coding</li><li>Think aloud — explain your approach</li><li>Start with brute force, then optimize</li><li>Test with edge cases: empty input, large n</li></ol><h4>System Design Starter</h4><p>Ask: Scale? Users? Features? Then: Load balancer → API → Database → Cache → CDN.</p>"},
            {"title": "Resume Writing & LinkedIn Optimization", "content_type": "text", "duration_min": 25, "content_text": "<h4>Resume Tips</h4><ul><li>1 page for freshers, ATS-friendly format</li><li>Use action verbs: Built, Designed, Improved, Led</li><li>Quantify impact: 'Reduced loading time by 40%'</li><li>Tailor keywords to each job description</li></ul><h4>LinkedIn</h4><ul><li>Professional photo, headline = Role + Value</li><li>All-Star profile with 500+ connections</li><li>Post projects and achievements regularly</li></ul>"},
            {"title": "Salary Negotiation & Offer Evaluation", "content_type": "text", "duration_min": 20, "content_text": "<h4>Salary Negotiation</h4><p>Research: Glassdoor, Levels.fyi, AmbitionBox.</p><p>Script: 'Based on my research and skills, I was expecting around ₹X LPA. Is there flexibility?'</p><h4>Evaluate an Offer</h4><ul><li>Base salary + Variable + Equity + Benefits</li><li>Growth trajectory, learning culture</li><li>Work-life balance and remote options</li></ul>"},
        ],
        "quiz": {
            "title": "Interview Preparation Quiz",
            "pass_percent": 60,
            "questions": [
                {"q": "What does STAR stand for in interview technique?", "a": "Skill, Task, Action, Result", "b": "Situation, Task, Action, Result", "c": "Situation, Topic, Achievement, Reason", "d": "Story, Task, Answer, Response", "ans": "B", "exp": "STAR = Situation, Task, Action, Result — a structured way to answer behavioral questions."},
                {"q": "What should you do FIRST in a coding interview?", "a": "Start coding immediately", "b": "Ask for hints", "c": "Clarify the problem and constraints", "d": "Write test cases", "ans": "C", "exp": "Always clarify the problem, inputs, outputs, and edge cases before writing any code."},
                {"q": "The best way to handle 'What is your weakness?'", "a": "Say you have no weaknesses", "b": "Mention a strength as a weakness", "c": "Share a real weakness with steps you are taking to improve", "d": "Refuse to answer", "ans": "C", "exp": "Honest + growth mindset answer shows self-awareness and maturity."},
                {"q": "ATS stands for?", "a": "Automated Test System", "b": "Applicant Tracking System", "c": "Application Template Standard", "d": "Automated Talent Screening", "ans": "B", "exp": "ATS = Applicant Tracking System, used by companies to screen resumes automatically."},
                {"q": "Which is the best LinkedIn profile headline for a fresher?", "a": "Student", "b": "Looking for Job", "c": "Final Year CS Student | Python & Django | Open to Opportunities", "d": "Unemployed", "ans": "C", "exp": "A specific headline with skills and status attracts recruiters and appears in search results."},
            ],
        },
    },
]


class Command(BaseCommand):
    help = 'Seed the Learning Hub with 10 placement-ready courses, lessons, and quizzes.'

    def handle(self, *args, **options):
        from courses.models import LearningCourse, Lesson, Quiz, QuizQuestion

        created_courses = 0
        created_lessons = 0
        created_quizzes = 0
        created_questions = 0

        for order, data in enumerate(COURSES_DATA, start=1):
            slug = slugify(data['title'])
            course, c_created = LearningCourse.objects.get_or_create(
                slug=slug,
                defaults={
                    'title':        data['title'],
                    'category':     data['category'],
                    'level':        data['level'],
                    'icon':         data['icon'],
                    'icon_color':   data['icon_color'],
                    'icon_bg':      data['icon_bg'],
                    'duration_hrs': data['duration_hrs'],
                    'description':  data['description'],
                    'objectives':   data['objectives'],
                    'order':        order,
                    'is_published': True,
                }
            )
            if c_created:
                created_courses += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created course: {course.title}'))
            else:
                self.stdout.write(f'  → Course already exists: {course.title}')

            # Lessons
            for lesson_order, lesson_data in enumerate(data['lessons'], start=1):
                lesson, l_created = Lesson.objects.get_or_create(
                    course=course,
                    title=lesson_data['title'],
                    defaults={
                        'order':        lesson_order,
                        'content_type': lesson_data.get('content_type', 'text'),
                        'content_text': lesson_data.get('content_text', ''),
                        'video_url':    lesson_data.get('video_url', ''),
                        'duration_min': lesson_data.get('duration_min', 15),
                        'is_published': True,
                    }
                )
                if l_created:
                    created_lessons += 1

            # Quiz
            quiz_data = data.get('quiz')
            if quiz_data:
                quiz, q_created = Quiz.objects.get_or_create(
                    course=course,
                    defaults={
                        'title':        quiz_data['title'],
                        'pass_percent': quiz_data.get('pass_percent', 60),
                    }
                )
                if q_created:
                    created_quizzes += 1

                for q_order, qd in enumerate(quiz_data['questions'], start=1):
                    qq, qq_created = QuizQuestion.objects.get_or_create(
                        quiz=quiz,
                        question=qd['q'],
                        defaults={
                            'option_a':    qd['a'],
                            'option_b':    qd['b'],
                            'option_c':    qd['c'],
                            'option_d':    qd['d'],
                            'answer':      qd['ans'],
                            'explanation': qd.get('exp', ''),
                            'order':       q_order,
                        }
                    )
                    if qq_created:
                        created_questions += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'✅ Seeding complete!\n'
            f'   Courses created:   {created_courses}\n'
            f'   Lessons created:   {created_lessons}\n'
            f'   Quizzes created:   {created_quizzes}\n'
            f'   Questions created: {created_questions}'
        ))
