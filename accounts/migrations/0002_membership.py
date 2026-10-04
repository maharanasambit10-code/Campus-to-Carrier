from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_free_memberships(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Membership = apps.get_model('accounts', 'Membership')
    Membership.objects.bulk_create(
        Membership(user_id=user_id, plan='FREE', status='ACTIVE')
        for user_id in User.objects.values_list('id', flat=True)
    )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan', models.CharField(choices=[('FREE', 'Free'), ('PRO_MONTHLY', 'PRO Monthly'), ('PRO_ANNUAL', 'PRO Annual')], default='FREE', max_length=20)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('PENDING', 'Pending payment'), ('EXPIRED', 'Expired'), ('CANCELLED', 'Cancelled')], default='ACTIVE', max_length=15)),
                ('current_period_start', models.DateTimeField(blank=True, null=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('provider', models.CharField(blank=True, max_length=30)),
                ('provider_customer_id', models.CharField(blank=True, max_length=160)),
                ('provider_subscription_id', models.CharField(blank=True, max_length=160)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='membership', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-updated_at',)},
        ),
        migrations.RunPython(create_free_memberships, migrations.RunPython.noop),
    ]