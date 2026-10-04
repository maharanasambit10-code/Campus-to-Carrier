import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('applications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Interview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_name', models.CharField(default='Technical Interview', max_length=120)),
                ('scheduled_at', models.DateTimeField()),
                ('duration_minutes', models.PositiveIntegerField(default=45)),
                ('mode', models.CharField(choices=[('ONLINE', 'Online'), ('ONSITE', 'Onsite')], default='ONLINE', max_length=10)),
                ('meeting_link', models.URLField(blank=True)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('SCHEDULED', 'Scheduled'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='SCHEDULED', max_length=15)),
                ('interviewer_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interviews', to='applications.application')),
            ],
            options={'ordering': ['scheduled_at']},
        ),
    ]
