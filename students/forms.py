import os

from django import forms

from .models import Achievement, Certification, Internship, Project, Skill, StudentProfile, StudentSkill


class StudentProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    skills = forms.CharField(required=False, help_text='Separate skills with commas.')

    class Meta:
        model = StudentProfile
        fields = [
            'phone', 'department', 'college', 'graduation_year', 'cgpa',
            'tenth_percentage', 'twelfth_percentage', 'location', 'about_me',
            'career_objective', 'linkedin', 'github', 'portfolio', 'resume',
            'headline', 'degree', 'education_start_year',
            'leetcode',
            'codechef', 'hackerrank', 'twitter', 'tenth_school', 'tenth_year',
            'twelfth_college', 'twelfth_year', 'profile_visibility', 'profile_photo',
        ]
        widgets = {
            'about_me': forms.Textarea(attrs={'rows': 3}),
            'career_objective': forms.Textarea(attrs={'rows': 3}),
            'graduation_year': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
            'cgpa': forms.NumberInput(attrs={'min': 0, 'max': 10, 'step': '0.01'}),
            'tenth_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': '0.01'}),
            'twelfth_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': '0.01'}),
            'profile_photo': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
            'resume': forms.ClearableFileInput(attrs={'accept': 'application/pdf,.docx'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        self.fields['profile_visibility'].required = False
        if self.instance and self.instance.profile_visibility:
            self.fields['profile_visibility'].initial = self.instance.profile_visibility
        if self.instance and self.instance.pk:
            self.fields['skills'].initial = ', '.join(
                self.instance.studentskill_set.select_related('skill').values_list('skill__name', flat=True)
            )
        self.order_fields([
            'phone', 'department', 'college', 'graduation_year', 'cgpa',
            'tenth_percentage', 'twelfth_percentage', 'location', 'about_me',
            'career_objective', 'skills', 'github', 'linkedin', 'portfolio',
            'resume', 'profile_photo', 'headline', 'degree', 'education_start_year',
            'leetcode', 'codechef', 'hackerrank', 'twitter', 'tenth_school',
            'tenth_year', 'twelfth_college', 'twelfth_year', 'profile_visibility',
            'first_name', 'last_name', 'email',
        ])
        for field in self.fields.values():
            if not isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if not self.cleaned_data.get('profile_visibility'):
            profile.profile_visibility = self.instance.profile_visibility or 'VERIFIED_RECRUITERS'
            if commit:
                profile.save(update_fields=['profile_visibility'])
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save(update_fields=['first_name', 'last_name', 'email'])
            skill_names = {
                name.strip().title()
                for name in self.cleaned_data.get('skills', '').split(',')
                if name.strip()
            }
            existing_skills = {
                student_skill.skill.name: student_skill
                for student_skill in profile.studentskill_set.select_related('skill')
            }
            for skill_name in skill_names - existing_skills.keys():
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                StudentSkill.objects.create(student=profile, skill=skill)
            profile.studentskill_set.exclude(skill__name__in=skill_names).delete()
        return profile

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if not photo:
            return photo

        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Profile photo must be 5 MB or smaller.')

        allowed_types = {'image/jpeg', 'image/jpg', 'image/png'}
        extension = os.path.splitext(photo.name)[1].lower()
        allowed_extensions = {'.jpg', '.jpeg', '.png'}
        if photo.content_type not in allowed_types and extension not in allowed_extensions:
            raise forms.ValidationError('Upload a JPG, JPEG, or PNG profile photo.')

        return photo

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume and resume.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Resume must be 10 MB or smaller.')
        allowed_types = {'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        allowed_extensions = {'.pdf', '.docx'}
        extension = os.path.splitext(resume.name)[1].lower() if resume else ''
        if resume and resume.content_type not in allowed_types and extension not in allowed_extensions:
            raise forms.ValidationError('Upload your resume as a PDF or DOCX file.')
        if resume:
            header = resume.read(8)
            resume.seek(0)
            if extension == '.pdf' and not header.startswith(b'%PDF'):
                raise forms.ValidationError('The uploaded file is not a valid PDF.')
            if extension == '.docx' and not header.startswith(b'PK'):
                raise forms.ValidationError('The uploaded file is not a valid DOCX file.')
        return resume


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'technologies', 'project_type', 'role', 'github_url', 'live_demo_url', 'image', 'start_date', 'end_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('End date cannot be before the start date.')
        return cleaned_data

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Project image must be 5 MB or smaller.')
        if image and image.content_type not in {'image/jpeg', 'image/png'}:
            raise forms.ValidationError('Upload a JPG or PNG project image.')
        return image


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'issuer', 'issue_date', 'credential_id', 'credential_url', 'certificate_file']
        widgets = {'issue_date': forms.DateInput(attrs={'type': 'date'}), 'certificate_file': forms.ClearableFileInput(attrs={'accept': 'application/pdf,image/jpeg,image/png'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_certificate_file(self):
        certificate = self.cleaned_data.get('certificate_file')
        if certificate and certificate.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Certificate files must be 10 MB or smaller.')
        return certificate


class InternshipForm(forms.ModelForm):
    class Meta:
        model = Internship
        fields = ['company', 'role', 'employment_type', 'location', 'start_date', 'end_date', 'description', 'skills_used']
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}), 'end_date': forms.DateInput(attrs={'type': 'date'}), 'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['title', 'description', 'achieved_on', 'organization', 'proof_url']
        widgets = {'achieved_on': forms.DateInput(attrs={'type': 'date'}), 'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'