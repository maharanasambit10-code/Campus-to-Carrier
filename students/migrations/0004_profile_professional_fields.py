import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_alter_project_options_project_end_date_project_image_and_more'),
    ]

    operations = [
        migrations.AddField(model_name='studentprofile', name='degree', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='studentprofile', name='education_start_year', field=models.IntegerField(blank=True, null=True)),
        migrations.AddField(model_name='studentprofile', name='headline', field=models.CharField(blank=True, max_length=180)),
        migrations.AddField(model_name='studentprofile', name='tenth_school', field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name='studentprofile', name='tenth_year', field=models.IntegerField(blank=True, null=True)),
        migrations.AddField(model_name='studentprofile', name='twelfth_college', field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name='studentprofile', name='twelfth_year', field=models.IntegerField(blank=True, null=True)),
        migrations.AddField(model_name='studentprofile', name='codechef', field=models.URLField(blank=True)),
        migrations.AddField(model_name='studentprofile', name='hackerrank', field=models.URLField(blank=True)),
        migrations.AddField(model_name='studentprofile', name='twitter', field=models.URLField(blank=True)),
        migrations.AddField(model_name='studentprofile', name='profile_visibility', field=models.CharField(choices=[('VERIFIED_RECRUITERS', 'Public to Verified Recruiters'), ('PRIVATE', 'Private'), ('APPLICATIONS_ONLY', 'Only During Applications')], default='VERIFIED_RECRUITERS', max_length=24)),
        migrations.AddField(model_name='project', name='project_type', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='project', name='role', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='internship', name='employment_type', field=models.CharField(choices=[('INTERNSHIP', 'Internship'), ('FULL_TIME', 'Full-time'), ('PART_TIME', 'Part-time'), ('FREELANCE', 'Freelance')], default='INTERNSHIP', max_length=20)),
        migrations.AddField(model_name='internship', name='location', field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name='internship', name='start_date', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='internship', name='end_date', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='internship', name='skills_used', field=models.CharField(blank=True, max_length=300)),
        migrations.AddField(model_name='certification', name='issue_date', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='certification', name='credential_id', field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name='certification', name='credential_url', field=models.URLField(blank=True)),
        migrations.AddField(model_name='certification', name='certificate_file', field=models.FileField(blank=True, null=True, upload_to='certifications/')),
        migrations.AlterField(model_name='certification', name='student', field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certifications', to='students.studentprofile')),
        migrations.CreateModel(
            name='Achievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('achieved_on', models.DateField(blank=True, null=True)),
                ('organization', models.CharField(blank=True, max_length=200)),
                ('proof_url', models.URLField(blank=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='achievements', to='students.studentprofile')),
            ],
            options={'ordering': ['-achieved_on', '-id']},
        ),
    ]
