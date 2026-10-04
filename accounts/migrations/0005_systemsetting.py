from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_payment_phonepe_merchant_transaction_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_mode', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'System Settings',
            },
        ),
    ]
