import os
import re

from django import forms
from django.contrib.auth.password_validation import validate_password

from accounts.models import User
from students.models import Skill, StudentProfile, StudentSkill


class StudentAccountForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control auth-input')
        self.fields['first_name'].widget.attrs['placeholder'] = 'Your first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Your last name'
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['email'].widget.attrs['placeholder'] = 'you@example.com'
        self.fields['phone'].widget.attrs['placeholder'] = '10-digit phone number'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and not re.fullmatch(r'[0-9+()\-\s]{7,20}', phone):
            raise forms.ValidationError('Enter a valid phone number.')
        return phone

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def create_user(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'].strip(),
            last_name=data.get('last_name', '').strip(),
            role='STUDENT',
        )
        StudentProfile.objects.create(user=user, phone=data.get('phone', '').strip())
        return user


class StudentProfileRegistrationForm(forms.ModelForm):
    skills = forms.CharField(help_text='Separate skills with commas.')
    resume = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'accept': 'application/pdf'}))
    profile_photo = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}))

    class Meta:
        model = StudentProfile
        fields = [
            'college', 'degree', 'department', 'specialization', 'current_semester',
            'graduation_year', 'cgpa', 'skills', 'preferred_job_role', 'job_type',
            'preferred_work_location', 'linkedin', 'github', 'portfolio', 'resume',
            'profile_photo',
        ]
        widgets = {
            'current_semester': forms.NumberInput(attrs={'min': 1, 'max': 12, 'placeholder': 'e.g. 6'}),
            'graduation_year': forms.NumberInput(attrs={'min': 2000, 'max': 2100, 'placeholder': 'e.g. 2027'}),
            'cgpa': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': '0.01', 'placeholder': 'e.g. 8.5 or 85'}),
            'college': forms.TextInput(attrs={'placeholder': 'Your college or university'}),
            'degree': forms.TextInput(attrs={'placeholder': 'e.g. B.Tech'}),
            'department': forms.TextInput(attrs={'placeholder': 'e.g. Computer Science'}),
            'specialization': forms.TextInput(attrs={'placeholder': 'e.g. AI and Machine Learning'}),
            'preferred_job_role': forms.TextInput(attrs={'placeholder': 'e.g. Backend Developer'}),
            'linkedin': forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/your-name'}),
            'github': forms.URLInput(attrs={'placeholder': 'https://github.com/your-name'}),
            'portfolio': forms.URLInput(attrs={'placeholder': 'https://yourportfolio.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['college'].required = True
        self.fields['degree'].required = True
        self.fields['department'].required = True
        self.fields['graduation_year'].required = True
        self.fields['skills'].required = True
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean_graduation_year(self):
        year = self.cleaned_data['graduation_year']
        if year < 2000 or year > 2100:
            raise forms.ValidationError('Enter a valid graduation year.')
        return year

    def clean_cgpa(self):
        cgpa = self.cleaned_data.get('cgpa')
        if cgpa is not None and cgpa > 100:
            raise forms.ValidationError('CGPA or percentage must be 100 or less.')
        return cgpa

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if not resume:
            return resume
        if resume.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Resume must be 10 MB or smaller.')
        if os.path.splitext(resume.name)[1].lower() != '.pdf' or resume.content_type != 'application/pdf':
            raise forms.ValidationError('Upload your resume as a PDF file.')
        header = resume.read(5)
        resume.seek(0)
        if not header.startswith(b'%PDF'):
            raise forms.ValidationError('The uploaded file is not a valid PDF.')
        return resume

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo and photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Profile photo must be 5 MB or smaller.')
        return photo

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            skill_names = {name.strip().title() for name in self.cleaned_data['skills'].split(',') if name.strip()}
            profile.studentskill_set.all().delete()
            for skill_name in skill_names:
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                StudentSkill.objects.create(student=profile, skill=skill)
        return profile


class StudentRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    phone = forms.CharField(max_length=20, required=False)
    college = forms.CharField(max_length=200, required=False)
    department = forms.CharField(max_length=100, required=False)
    degree = forms.CharField(max_length=120, required=False)
    specialization = forms.CharField(max_length=160, required=False)
    current_semester = forms.IntegerField(required=False, min_value=1, max_value=12)
    graduation_year = forms.IntegerField(required=False, min_value=2000, max_value=2100)
    cgpa = forms.FloatField(required=False, min_value=0, max_value=100)
    skills = forms.CharField(required=False)
    preferred_job_role = forms.CharField(max_length=160, required=False)
    job_type = forms.ChoiceField(choices=StudentProfile.JOB_TYPE_CHOICES, required=False)
    preferred_work_location = forms.ChoiceField(choices=StudentProfile.WORK_LOCATION_CHOICES, required=False)
    linkedin = forms.URLField(required=False)
    github = forms.URLField(required=False)
    portfolio = forms.URLField(required=False)
    resume = forms.FileField(required=False)
    profile_photo = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'confirm_password', 'phone', 'college', 'department']
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'username'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and not re.fullmatch(r'[0-9+()\-\s]{7,20}', phone):
            raise forms.ValidationError('Enter a valid phone number.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data.get('last_name', '').strip()
        user.email = self.cleaned_data['email']
        user.role = 'STUDENT'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            profile = StudentProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', '').strip(),
                college=self.cleaned_data.get('college', '').strip(),
                department=self.cleaned_data.get('department', '').strip(),
                degree=self.cleaned_data.get('degree', '').strip(),
                specialization=self.cleaned_data.get('specialization', '').strip(),
                current_semester=self.cleaned_data.get('current_semester'),
                graduation_year=self.cleaned_data.get('graduation_year'),
                cgpa=self.cleaned_data.get('cgpa'),
                preferred_job_role=self.cleaned_data.get('preferred_job_role', '').strip(),
                job_type=self.cleaned_data.get('job_type', ''),
                preferred_work_location=self.cleaned_data.get('preferred_work_location', ''),
                linkedin=self.cleaned_data.get('linkedin', '').strip(),
                github=self.cleaned_data.get('github', '').strip(),
                portfolio=self.cleaned_data.get('portfolio', '').strip(),
            )
            skill_names = {name.strip().title() for name in self.cleaned_data.get('skills', '').split(',') if name.strip()}
            for skill_name in skill_names:
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                StudentSkill.objects.create(student=profile, skill=skill)
        return user
