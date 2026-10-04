
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models


PRO_PLAN_PRICING = {
    'PRO_MONTHLY': {
        'label': 'PRO Monthly',
        'amount': Decimal('1.00'),
        'currency': 'INR',
        'period_days': 30,
    },
    'PRO_ANNUAL': {
        'label': 'PRO Annual',
        'amount': Decimal('1999.00'),
        'currency': 'INR',
        'period_days': 365,
    },
}


class User(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('PLACEMENT_OFFICER', 'Placement Officer'),
        ('RECRUITER', 'Recruiter'),
        ('SUPER_ADMIN', 'Super Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')

    @property
    def plan(self):
        membership = getattr(self, 'membership', None)
        return 'pro' if (membership and membership.is_active) else 'free'

    @property
    def is_pro(self):
        return self.plan == 'pro'

    @property
    def pro_expiry(self):
        membership = getattr(self, 'membership', None)
        return membership.current_period_end if (membership and membership.is_active) else None


class Membership(models.Model):
    PLAN_CHOICES = (
        ('FREE', 'Free'),
        ('PRO_MONTHLY', 'PRO Monthly'),
        ('PRO_ANNUAL', 'PRO Annual'),
    )
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending payment'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='membership')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='FREE')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    start_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    provider = models.CharField(max_length=30, blank=True)
    provider_customer_id = models.CharField(max_length=160, blank=True)
    provider_subscription_id = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)

    @property
    def is_active(self):
        from django.utils import timezone

        return (
            self.plan != 'FREE'
            and self.status == 'ACTIVE'
            and (self.current_period_end is None or self.current_period_end > timezone.now())
        )

    @property
    def is_pro(self):
        return self.is_active

    def cancel_subscription(self):
        self.status = 'CANCELLED'
        self.save(update_fields=['status', 'updated_at'])

    def is_expiring_soon(self, days=3):
        from django.utils import timezone
        from datetime import timedelta
        if not self.is_active or not self.current_period_end:
            return False
        return self.current_period_end <= timezone.now() + timedelta(days=days)

    def __str__(self):
        return f'{self.user.username} - {self.get_plan_display()}'


class Payment(models.Model):
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.CharField(max_length=20, choices=Membership.PLAN_CHOICES, default='FREE')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='created')
    phonepe_merchant_transaction_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    phonepe_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=255, blank=True, db_index=True, unique=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, db_index=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    provider = models.CharField(max_length=30, default='PHONEPE', blank=True)
    payment_reference = models.CharField(max_length=255, blank=True, help_text='UPI reference, transaction ID, or payment note.')
    payment_proof = models.URLField(blank=True, help_text='Optional receipt or proof URL.')
    notes = models.TextField(blank=True, help_text='Internal admin notes for manual verification.')
    manual_verified_at = models.DateTimeField(null=True, blank=True)
    manual_verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_payments')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['plan', 'status']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.plan} - {self.status}'


def get_pro_plan_pricing(plan):
    if plan not in PRO_PLAN_PRICING:
        raise ValueError(f'Unsupported plan: {plan}')
    data = PRO_PLAN_PRICING[plan].copy()
    data['amount_in_paise'] = int((data['amount'] * 100).quantize(Decimal('1')))
    return data


class SystemSetting(models.Model):
    maintenance_mode = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'System Settings'
        
    def __str__(self):
        return f"System Settings (Maintenance: {self.maintenance_mode})"
