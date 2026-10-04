from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='industry',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='company',
            name='locations',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='company',
            name='hiring_process',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='company',
            name='verification_status',
            field=models.CharField(choices=[('PENDING', 'Verification Pending'), ('VERIFIED', 'Verified Company'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20),
        ),
        migrations.AddField(
            model_name='company',
            name='is_demo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='company',
            name='open_positions',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='company',
            name='internship_opportunities',
            field=models.IntegerField(default=0),
        ),
    ]
