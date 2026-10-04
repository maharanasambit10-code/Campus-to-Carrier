import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlacementDrive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('PLANNED', 'Planned'), ('OPEN', 'Open'), ('CLOSED', 'Closed')], default='PLANNED', max_length=10)),
                ('coordinator_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='placement_drives', to='companies.company')),
                ('jobs', models.ManyToManyField(blank=True, related_name='placement_drives', to='jobs.job')),
            ],
            options={'ordering': ['-start_date']},
        ),
    ]
