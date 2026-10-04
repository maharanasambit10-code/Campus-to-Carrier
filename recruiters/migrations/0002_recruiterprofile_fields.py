from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruiters', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recruiterprofile',
            name='verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='recruiterprofile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default='2026-01-01T00:00:00Z'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recruiterprofile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
