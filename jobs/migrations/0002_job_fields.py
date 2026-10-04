import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='min_tenth',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='job',
            name='min_twelfth',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='job',
            name='allowed_departments',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='job',
            name='work_mode',
            field=models.CharField(choices=[('Onsite', 'Onsite'), ('Hybrid', 'Hybrid'), ('Remote', 'Remote')], default='Onsite', max_length=20),
        ),
        migrations.AddField(
            model_name='job',
            name='internship_type',
            field=models.CharField(choices=[('Full-Time', 'Full-Time'), ('Internship', 'Internship'), ('Contract', 'Contract')], default='Full-Time', max_length=20),
        ),
        migrations.AddField(
            model_name='job',
            name='is_verified',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='job',
            name='preferred_skills',
            field=models.ManyToManyField(blank=True, related_name='preferred_jobs', to='students.skill'),
        ),

        migrations.AlterField(
            model_name='job',
            name='graduation_year',
            field=models.IntegerField(default=2026),
        ),
    ]
