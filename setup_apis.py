import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")

# 1. Accounts API
with open(BASE_DIR / "accounts" / "serializers.py", "w") as f:
    f.write("from rest_framework import serializers\nfrom .models import User\nclass UserSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = User\n        fields = ['id', 'username', 'email', 'role']\n")

# 2. Students API
with open(BASE_DIR / "students" / "serializers.py", "w") as f:
    f.write("from rest_framework import serializers\nfrom .models import StudentProfile, Skill\nclass SkillSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = Skill\n        fields = '__all__'\nclass StudentSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = StudentProfile\n        fields = '__all__'\n")

with open(BASE_DIR / "students" / "views.py", "w") as f:
    f.write("from rest_framework import viewsets\nfrom .models import StudentProfile\nfrom .serializers import StudentSerializer\nclass StudentViewSet(viewsets.ModelViewSet):\n    queryset = StudentProfile.objects.all()\n    serializer_class = StudentSerializer\n")

# 3. Jobs API
with open(BASE_DIR / "jobs" / "serializers.py", "w") as f:
    f.write("from rest_framework import serializers\nfrom .models import Job\nclass JobSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = Job\n        fields = '__all__'\n")

with open(BASE_DIR / "jobs" / "views.py", "w") as f:
    f.write("from rest_framework import viewsets\nfrom .models import Job\nfrom .serializers import JobSerializer\nclass JobViewSet(viewsets.ModelViewSet):\n    queryset = Job.objects.all()\n    serializer_class = JobSerializer\n")

# 4. Global URL Routing
urls_code = """
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from students.views import StudentViewSet
from jobs.views import JobViewSet
from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'api/students', StudentViewSet)
router.register(r'api/jobs', JobViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('', include(router.urls)),
]
"""
with open(BASE_DIR / "campuslink" / "urls.py", "w") as f:
    f.write(urls_code)

print("APIs configured successfully!")
