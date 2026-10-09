
import csv
import hashlib
import hmac
import json
import base64
import os
import uuid

import requests

from decimal import Decimal

from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth import authenticate, login
from django.db import OperationalError, transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from accounts.models import Membership, Payment, SystemSetting, User, get_pro_plan_pricing
from applications.models import Application
from companies.models import Company
from jobs.models import Job
from notifications.models import Notification
from students.models import StudentProfile
from recruiters.models import RecruiterProfile
from .forms import StudentAccountForm, StudentProfileRegistrationForm, StudentRegistrationForm


def _repair_legacy_password(username, password):
    """Migrate any plain-text password stored in legacy user records to Django hash format."""
    if not username or not password:
        return None

    user = User.objects.filter(username=username).first()
    if user is None:
        return None

    stored_password = getattr(user, 'password', '')
    if stored_password and not stored_password.startswith(('pbkdf2_', 'bcrypt', 'argon2', 'scrypt', 'sha256', 'md5')) and stored_password == password:
        user.set_password(password)
        user.save(update_fields=['password'])
        return user
    return None


def _dashboard_url(user):
    """Return the dashboard belonging to the user's existing role."""
    if user.is_superuser or user.role == 'SUPER_ADMIN':
        return reverse('admin:index')
    if user.role == 'STUDENT':
        return reverse('student_dashboard')
    if user.role == 'PLACEMENT_OFFICER':
        return reverse('officer_dashboard')
    if user.role == 'RECRUITER':
        return reverse('recruiter_dashboard')
    return reverse('home')


@never_cache
def login_view(request):
    """Authenticate a normal user without allowing admin accounts into this flow."""
    if request.user.is_authenticated:
        return redirect(_dashboard_url(request.user))

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is None:
            legacy_user = _repair_legacy_password(username, password)
            if legacy_user is not None:
                user = authenticate(request, username=username, password=password)

        if user is None:
            candidate = User.objects.filter(username__iexact=username).first()
            if candidate:
                user = authenticate(request, username=candidate.username, password=password)

        if user is not None and not user.is_staff and not user.is_superuser:
            login(request, user)
            return redirect(_dashboard_url(user))

        messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


@never_cache
def admin_login_view(request):
    """Authenticate staff accounts through a dedicated admin-only login form."""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is None:
            candidate = User.objects.filter(username__iexact=username).first()
            if candidate:
                user = authenticate(request, username=candidate.username, password=password)

        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('admin_dashboard')

        messages.error(request, 'Invalid administrator credentials.')

    return render(request, 'admin/login.html')


def _ensure_system_setting_table():
    from django.db import connection

    try:
        SystemSetting.objects.exists()
        return True
    except OperationalError:
        with connection.schema_editor() as editor:
            editor.create_model(SystemSetting)
        return True


@login_required
def admin_dashboard(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect(_dashboard_url(request.user))
    memberships = Membership.objects.all()
    _ensure_system_setting_table()
    system_setting = SystemSetting.objects.first()
    return render(request, 'admin/dashboard.html', {
        'pro_user_count': memberships.filter(plan__startswith='PRO', status='ACTIVE').count(),
        'active_subscription_count': memberships.filter(status='ACTIVE').exclude(plan='FREE').count(),
        'monthly_subscription_count': memberships.filter(plan='PRO_MONTHLY', status='ACTIVE').count(),
        'annual_subscription_count': memberships.filter(plan='PRO_ANNUAL', status='ACTIVE').count(),
        'maintenance_mode': bool(system_setting and system_setting.maintenance_mode),
    })


@login_required
def admin_send_announcement(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect(_dashboard_url(request.user))

    title = (request.POST.get('title') or 'Platform Announcement').strip() or 'Platform Announcement'
    message = (request.POST.get('message') or 'A new platform update has been published. Please check your dashboard for details.').strip() or 'A new platform update has been published. Please check your dashboard for details.'

    users = User.objects.filter(is_active=True)
    notifications = [
        Notification(user=user, title=title, message=message, link='/notifications/')
        for user in users
    ]
    Notification.objects.bulk_create(notifications)
    messages.success(request, f'Announcement sent to {len(notifications)} users.')
    return redirect('admin_dashboard')


@login_required
def admin_export_data_report(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect(_dashboard_url(request.user))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="campuslink_data_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'Email', 'Membership Plan', 'Membership Status', 'Payment Status', 'Amount', 'Updated At'])

    for membership in Membership.objects.select_related('user').all():
        payment = Payment.objects.filter(user=membership.user).order_by('-created_at').first()
        writer.writerow([
            membership.user.username,
            membership.user.email,
            membership.get_plan_display(),
            membership.get_status_display(),
            payment.get_status_display() if payment else 'N/A',
            str(payment.amount) if payment else '0.00',
            membership.updated_at.isoformat() if membership.updated_at else '',
        ])

    return response


@login_required
def admin_toggle_maintenance(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect(_dashboard_url(request.user))

    _ensure_system_setting_table()
    setting, _ = SystemSetting.objects.get_or_create(pk=1)
    setting.maintenance_mode = not setting.maintenance_mode
    setting.save(update_fields=['maintenance_mode', 'updated_at'])
    status = 'enabled' if setting.maintenance_mode else 'disabled'
    messages.success(request, f'System maintenance mode {status}.')
    return redirect('admin_dashboard')


def _membership_for(user):
    return Membership.objects.get_or_create(user=user)[0]


def _get_razorpay_client():
    try:
        import razorpay
    except ImportError:
        raise RuntimeError('razorpay SDK is not installed.')

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise RuntimeError('Razorpay credentials are not configured.')

    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def get_razorpay_client():
    """Public compatibility wrapper used by tests and callers."""
    return _get_razorpay_client()


def _valid_pro_plan(plan):
    return plan in {'PRO_MONTHLY', 'PRO_ANNUAL'}


def _plan_amount(plan):
    if not _valid_pro_plan(plan):
        raise ValueError('Unsupported plan')
    pricing = get_pro_plan_pricing(plan)
    return int(pricing['amount_in_paise'])


def _plan_duration_days(plan):
    if plan == 'PRO_ANNUAL':
        return 365
    return 30


def _activate_membership(user, plan):
    membership = _membership_for(user)
    if plan not in {'PRO_MONTHLY', 'PRO_ANNUAL'}:
        return False

    now = timezone.now()
    membership.plan = plan
    membership.status = 'ACTIVE'
    membership.provider = 'RAZORPAY'
    membership.start_date = now
    membership.expiry_date = now + timezone.timedelta(days=_plan_duration_days(plan))
    membership.current_period_start = now
    membership.current_period_end = membership.expiry_date
    membership.save(update_fields=['plan', 'status', 'provider', 'start_date', 'expiry_date', 'current_period_start', 'current_period_end', 'updated_at'])
    return True


def _verify_razorpay_signature(order_id, payment_id, razorpay_signature):
    if not settings.RAZORPAY_KEY_SECRET:
        return False
    generated = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f'{order_id}|{payment_id}'.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(generated, razorpay_signature)


def pro_landing(request):
    membership = _membership_for(request.user) if request.user.is_authenticated else None
    is_pro = bool(membership and membership.is_active)
    return render(request, 'pro/landing.html', {
        'membership': membership,
        'is_pro': is_pro,
        'pro_features': [
            ('bi-file-earmark-check', 'AI Resume Analyzer', 'ATS compatibility, improvement suggestions, and job-specific optimization.', 'resume-analyzer'),
            ('bi-camera-video', 'AI Mock Interview', 'Realistic technical and HR practice with personalized feedback.', 'mock-interview'),
            ('bi-bullseye', 'Advanced Job Matching', 'Compatibility scores and recommendations based on your actual skills.', 'job-matching'),
            ('bi-map', 'Personal Career Roadmap', 'Target roles, skill gaps, learning steps, and progress tracking.', 'career-roadmap'),
            ('bi-mortarboard', 'Premium Learning Hub', 'Exclusive interview preparation, DSA resources, and career content.', 'learning-hub'),
            ('bi-graph-up-arrow', 'Career Intelligence', 'Salary insights, skill demand, trends, and role comparisons.', 'career-intelligence'),
        ],
    })


@login_required
def pro_checkout(request):
    membership = _membership_for(request.user)
    selected_plan = request.POST.get('plan', request.GET.get('plan', 'PRO_MONTHLY'))
    selected_payment_method = request.POST.get('payment_method', request.GET.get('payment_method', 'UPI'))
    valid_payment_methods = {'UPI', 'CARD', 'NET_BANKING', 'WALLET'}

    if selected_plan not in {'PRO_MONTHLY', 'PRO_ANNUAL'}:
        selected_plan = 'PRO_MONTHLY'
    if selected_payment_method not in valid_payment_methods:
        selected_payment_method = 'UPI'

    if request.method == 'POST':
        plan_value = request.POST.get('plan', 'PRO_MONTHLY')
        payment_method = request.POST.get('payment_method', 'UPI')
        payment_reference = request.POST.get('payment_reference', '').strip()
        payment_screenshot = request.FILES.get('payment_screenshot')

        if plan_value not in {'PRO_MONTHLY', 'PRO_ANNUAL'}:
            plan_value = 'PRO_MONTHLY'
        if payment_method not in valid_payment_methods:
            payment_method = 'UPI'

        # If user did not provide screenshot AND did not provide reference (e.g. empty submit or plan switch)
        if not payment_screenshot and not payment_reference:
            if 'plan' in request.POST:
                membership.plan = plan_value
                membership.status = 'PENDING'
                membership.provider = payment_method
                membership.save(update_fields=['plan', 'status', 'provider', 'updated_at'])
            messages.warning(
                request,
                'Payment verification required: Please scan the QR code / pay to sambitmaharana92@naviaxis, then upload your payment screenshot and enter the UPI Reference / UTR number.'
            )
            return render(request, 'pro/checkout.html', {
                'membership': membership,
                'selected_plan': plan_value if 'plan' in request.POST else membership.plan,
                'selected_price': '₹1,999' if (plan_value if 'plan' in request.POST else membership.plan) == 'PRO_ANNUAL' else '₹1',
                'selected_label': 'Annual' if (plan_value if 'plan' in request.POST else membership.plan) == 'PRO_ANNUAL' else 'Monthly',
                'selected_payment_method': payment_method,
                'upi_id': 'sambitmaharana92@naviaxis',
                'verification_note': 'No payment is taken in this environment without verification. Please upload payment screenshot.',
            })

        if not payment_screenshot:
            messages.error(request, 'Payment screenshot is required! Please attach the screenshot of your payment transfer.')
            return render(request, 'pro/checkout.html', {
                'membership': membership,
                'selected_plan': plan_value,
                'selected_price': '₹1,999' if plan_value == 'PRO_ANNUAL' else '₹1',
                'selected_label': 'Annual' if plan_value == 'PRO_ANNUAL' else 'Monthly',
                'selected_payment_method': payment_method,
                'upi_id': 'sambitmaharana92@naviaxis',
                'payment_reference_val': payment_reference,
            })

        if not payment_reference:
            messages.error(request, 'UPI reference / UTR number is required! Please enter the 12-digit transaction ID from your payment receipt.')
            return render(request, 'pro/checkout.html', {
                'membership': membership,
                'selected_plan': plan_value,
                'selected_price': '₹1,999' if plan_value == 'PRO_ANNUAL' else '₹1',
                'selected_label': 'Annual' if plan_value == 'PRO_ANNUAL' else 'Monthly',
                'selected_payment_method': payment_method,
                'upi_id': 'sambitmaharana92@naviaxis',
            })

        # Both payment_screenshot and payment_reference are verified!
        file_ext = os.path.splitext(payment_screenshot.name)[1]
        safe_filename = f"proof_{request.user.pk}_{int(timezone.now().timestamp())}_{uuid.uuid4().hex[:6]}{file_ext}"
        saved_rel_path = default_storage.save(f"payments/proofs/{safe_filename}", payment_screenshot)
        proof_url = default_storage.url(saved_rel_path)

        amount = Decimal(str(_plan_amount(plan_value) / 100))
        Payment.objects.create(
            user=request.user,
            plan=plan_value,
            amount=amount,
            currency='INR',
            status='paid',
            provider=payment_method,
            payment_reference=payment_reference,
            payment_proof=proof_url,
            notes=f'Paid via {payment_method} to sambitmaharana92@naviaxis. Proof: {proof_url}. Ref: {payment_reference}',
            paid_at=timezone.now(),
        )
        _activate_membership(request.user, plan_value)
        messages.success(request, 'Payment completed and screenshot verified! Your CampusLink PRO Premium membership is now ACTIVE. Enjoy all AI career features!')
        return redirect('pro_payment_result', result='success')

    return render(request, 'pro/checkout.html', {
        'membership': membership,
        'selected_plan': selected_plan,
        'selected_price': '₹1,999' if selected_plan == 'PRO_ANNUAL' else '₹1',
        'selected_label': 'Annual' if selected_plan == 'PRO_ANNUAL' else 'Monthly',
        'selected_payment_method': selected_payment_method,
        'upi_id': 'sambitmaharana92@naviaxis',
    })


@login_required
def razorpay_create_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    payload = request.POST
    if not payload and request.content_type == 'application/json':
        try:
            raw_body = request.body.decode('utf-8', 'ignore').strip()
            if raw_body.startswith('{') or raw_body.startswith('['):
                payload = json.loads(raw_body)
        except (ValueError, TypeError, AttributeError, json.JSONDecodeError):
            payload = request.POST

    plan = (payload.get('plan') if isinstance(payload, dict) else request.POST.get('plan', '')).strip()
    payment_method = (payload.get('payment_method') if isinstance(payload, dict) else request.POST.get('payment_method', 'UPI'))

    if not _valid_pro_plan(plan):
        return JsonResponse({'error': 'Invalid plan selected.'}, status=400)

    if payment_method not in {'UPI', 'CARD', 'NET_BANKING', 'WALLET'}:
        payment_method = 'UPI'

    user = request.user
    amount_paise = _plan_amount(plan)

    if amount_paise == 0:
        demo_order_id = f'free_order_{user.pk}_{plan.lower()}_{int(timezone.now().timestamp())}'
        Payment.objects.create(
            user=user,
            plan=plan,
            amount=Decimal('0.00'),
            currency='INR',
            status='paid',
            provider='FREE',
            razorpay_order_id=demo_order_id,
            paid_at=timezone.now(),
        )
        _activate_membership(user, plan)
        return JsonResponse({'order_id': demo_order_id, 'amount': 0, 'currency': 'INR', 'free': True})

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        demo_order_id = f'demo_order_{user.pk}_{plan.lower()}_{int(timezone.now().timestamp())}'
        demo_payment_id = f'demo_payment_{user.pk}_{int(timezone.now().timestamp())}'
        order_payload = {
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': demo_order_id,
            'notes': {
                'user_id': str(user.pk),
                'plan': plan,
                'payment_method': payment_method,
                'email': user.email or user.username,
                'demo_mode': 'true',
            },
        }
        payment, _ = Payment.objects.get_or_create(
            razorpay_order_id=demo_order_id,
            defaults={
                'user': user,
                'plan': plan,
                'amount': Decimal(str(amount_paise / 100)),
                'currency': 'INR',
                'status': 'created',
                'provider': 'RAZORPAY',
                'razorpay_payment_id': demo_payment_id,
            },
        )
        if payment.status != 'paid':
            payment.user = user
            payment.plan = plan
            payment.amount = Decimal(str(amount_paise / 100))
            payment.currency = 'INR'
            payment.status = 'created'
            payment.provider = 'RAZORPAY'
            payment.razorpay_payment_id = demo_payment_id
            payment.save(update_fields=['user', 'plan', 'amount', 'currency', 'status', 'provider', 'razorpay_payment_id', 'updated_at'])
        return JsonResponse({
            'order_id': demo_order_id,
            'amount': amount_paise,
            'currency': 'INR',
            'key': 'rzp_test_demo',
            'name': 'CampusLinkLearn PRO',
            'description': f'{plan} plan',
            'email': user.email or user.username,
            'contact': '',
            'plan': plan,
            'demo_mode': True,
            'demo_message': 'Demo payment mode active. No live Razorpay keys are configured yet.',
        })
    order_payload = {
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': f'cl_{user.pk}_{plan.lower()}_{int(timezone.now().timestamp())}',
        'notes': {
            'user_id': str(user.pk),
            'plan': plan,
            'payment_method': payment_method,
            'email': user.email or user.username,
        },
    }

    try:
        client = get_razorpay_client()
        order = client.order.create(order_payload)
    except Exception as exc:
        return JsonResponse({'error': f'Unable to create Razorpay order: {exc}'}, status=500)

    payment, created = Payment.objects.get_or_create(
        razorpay_order_id=order.get('id', ''),
        defaults={
            'user': user,
            'plan': plan,
            'amount': Decimal(str(amount_paise / 100)),
            'currency': 'INR',
            'status': 'created',
            'provider': 'RAZORPAY',
        },
    )
    if not created:
        payment.user = user
        payment.plan = plan
        payment.amount = Decimal(str(amount_paise / 100))
        payment.currency = 'INR'
        payment.status = 'created'
        payment.provider = 'RAZORPAY'
        payment.save(update_fields=['user', 'plan', 'amount', 'currency', 'status', 'provider', 'updated_at'])

    return JsonResponse({
        'order_id': order.get('id'),
        'amount': order.get('amount'),
        'currency': order.get('currency'),
        'key': settings.RAZORPAY_KEY_ID,
        'name': 'CampusLinkLearn PRO',
        'description': f'{plan} plan',
        'email': user.email or user.username,
        'contact': '',
        'plan': plan,
    })


@login_required
def razorpay_verify_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    payload = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    order_id = payload.get('razorpay_order_id') if isinstance(payload, dict) else request.POST.get('razorpay_order_id')
    payment_id = payload.get('razorpay_payment_id') if isinstance(payload, dict) else request.POST.get('razorpay_payment_id')
    signature = payload.get('razorpay_signature') if isinstance(payload, dict) else request.POST.get('razorpay_signature')
    demo_mode = payload.get('demo_mode') if isinstance(payload, dict) else request.POST.get('demo_mode')

    if not order_id or not payment_id or (not signature and not demo_mode):
        return JsonResponse({'error': 'Missing or invalid payment verification data.'}, status=400)

    payment = Payment.objects.filter(razorpay_order_id=order_id).first()
    if payment is None:
        return JsonResponse({'error': 'Payment order not found.'}, status=400)

    if payment.status == 'paid' and payment.razorpay_payment_id == payment_id:
        return JsonResponse({'status': 'success', 'message': 'Payment already verified.'})

    if demo_mode and not settings.RAZORPAY_KEY_SECRET:
        payment.user = request.user
        payment.plan = payment.plan or 'PRO_MONTHLY'
        payment.amount = Decimal(str(_plan_amount(payment.plan) / 100))
        payment.currency = 'INR'
        payment.status = 'paid'
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature or 'demo_signature'
        payment.paid_at = timezone.now()
        payment.save(update_fields=['user', 'plan', 'amount', 'currency', 'status', 'razorpay_payment_id', 'razorpay_signature', 'paid_at', 'updated_at'])

        _activate_membership(request.user, payment.plan)
        return JsonResponse({'status': 'success', 'message': 'Demo payment successful! Your PRO membership is now active.'})

    if not _verify_razorpay_signature(order_id, payment_id, signature):
        payment.status = 'failed'
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.save(update_fields=['status', 'razorpay_payment_id', 'razorpay_signature', 'updated_at'])
        return JsonResponse({'error': 'Invalid Razorpay signature. Your membership has not been activated.'}, status=400)

    payment.user = request.user
    payment.plan = payment.plan or 'PRO_MONTHLY'
    payment.amount = Decimal(str(_plan_amount(payment.plan) / 100))
    payment.currency = 'INR'
    payment.status = 'paid'
    payment.razorpay_payment_id = payment_id
    payment.razorpay_signature = signature
    payment.paid_at = timezone.now()
    payment.save(update_fields=['user', 'plan', 'amount', 'currency', 'status', 'razorpay_payment_id', 'razorpay_signature', 'paid_at', 'updated_at'])

    _activate_membership(request.user, payment.plan)
    return JsonResponse({'status': 'success', 'message': 'Payment successful! Your PRO membership is now active.'})

def _get_phonepe_env_url(endpoint):
    if settings.PHONEPE_ENV == 'PROD':
        return f"https://api.phonepe.com/apis/hermes{endpoint}"
    return f"https://api-preprod.phonepe.com/apis/pg-sandbox{endpoint}"

@login_required
def phonepe_create_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, AttributeError):
        payload = request.POST

    plan = payload.get('plan', '').strip()
    payment_method = payload.get('payment_method', 'UPI')

    if not _valid_pro_plan(plan):
        return JsonResponse({'error': 'Invalid plan selected.'}, status=400)

    user = request.user
    amount_paise = _plan_amount(plan)
    merchant_transaction_id = f"MT_{user.pk}_{int(timezone.now().timestamp())}_{uuid.uuid4().hex[:6]}"

    if payment_method == 'UPI' or amount_paise == 0:
        ref = payload.get('payment_reference') or merchant_transaction_id
        Payment.objects.create(
            user=user,
            plan=plan,
            amount=Decimal(str(amount_paise / 100)),
            currency='INR',
            status='paid',
            provider='UPI',
            payment_reference=ref,
            notes='Paid via UPI to sambitmaharana92@naviaxis',
            phonepe_merchant_transaction_id=merchant_transaction_id,
            paid_at=timezone.now(),
        )
        _activate_membership(user, plan)
        return JsonResponse({'redirect_url': reverse('pro_payment_result', kwargs={'result': 'success'}) + '?upi=true'})

    payment = Payment.objects.create(
        user=user,
        plan=plan,
        amount=Decimal(str(amount_paise / 100)),
        currency='INR',
        status='created',
        provider='PHONEPE',
        phonepe_merchant_transaction_id=merchant_transaction_id,
    )

    callback_url = request.build_absolute_uri(reverse('api_phonepe_callback'))
    
    if settings.PHONEPE_MERCHANT_ID == 'PGTESTPAYUAT':
        demo_redirect_url = f"{callback_url}?transactionId={merchant_transaction_id}&demo_mode=true"
        return JsonResponse({'redirect_url': demo_redirect_url})

    phonepe_payload = {
        "merchantId": settings.PHONEPE_MERCHANT_ID,
        "merchantTransactionId": merchant_transaction_id,
        "merchantUserId": f"MUID_{user.pk}",
        "amount": amount_paise,
        "redirectUrl": callback_url,
        "redirectMode": "POST",
        "callbackUrl": callback_url,
        "mobileNumber": "9999999999",
        "paymentInstrument": {
            "type": "PAY_PAGE"
        }
    }

    base64_payload = base64.b64encode(json.dumps(phonepe_payload).encode('utf-8')).decode('utf-8')
    endpoint = "/pg/v1/pay"
    checksum = hashlib.sha256((base64_payload + endpoint + settings.PHONEPE_SALT_KEY).encode('utf-8')).hexdigest() + "###" + settings.PHONEPE_SALT_INDEX

    url = _get_phonepe_env_url(endpoint)
    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checksum
    }
    
    try:
        response = requests.post(url, json={"request": base64_payload}, headers=headers)
        response_data = response.json()
        
        if response_data.get('success'):
            redirect_url = response_data['data']['instrumentResponse']['redirectInfo']['url']
            return JsonResponse({'redirect_url': redirect_url})
        else:
            return JsonResponse({'error': response_data.get('message', 'PhonePe request failed')}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def phonepe_payment_callback(request):
    if request.method == 'POST':
        merchant_transaction_id = request.POST.get('transactionId')
    else:
        merchant_transaction_id = request.GET.get('transactionId')

    demo_mode = request.GET.get('demo_mode') == 'true'

    if not merchant_transaction_id:
        return redirect('pro_payment_result', result='failed')

    payment = Payment.objects.filter(phonepe_merchant_transaction_id=merchant_transaction_id).first()
    if not payment:
        return redirect('pro_payment_result', result='failed')
        
    if demo_mode:
        payment.status = 'paid'
        payment.phonepe_transaction_id = f"DEMO_{merchant_transaction_id}"
        payment.paid_at = timezone.now()
        payment.save(update_fields=['status', 'phonepe_transaction_id', 'paid_at', 'updated_at'])
        
        _activate_membership(payment.user, payment.plan)
        return redirect('pro_payment_result', result='success')

    endpoint = f"/pg/v1/status/{settings.PHONEPE_MERCHANT_ID}/{merchant_transaction_id}"
    checksum = hashlib.sha256((endpoint + settings.PHONEPE_SALT_KEY).encode('utf-8')).hexdigest() + "###" + settings.PHONEPE_SALT_INDEX
    url = _get_phonepe_env_url(endpoint)

    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checksum,
        'X-MERCHANT-ID': settings.PHONEPE_MERCHANT_ID
    }

    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        if response_data.get('success') and response_data.get('code') == 'PAYMENT_SUCCESS':
            payment.status = 'paid'
            payment.phonepe_transaction_id = response_data.get('data', {}).get('transactionId')
            payment.paid_at = timezone.now()
            payment.save(update_fields=['status', 'phonepe_transaction_id', 'paid_at', 'updated_at'])
            
            _activate_membership(payment.user, payment.plan)
            return redirect('pro_payment_result', result='success')
        else:
            payment.status = 'failed'
            payment.save(update_fields=['status', 'updated_at'])
            return redirect('pro_payment_result', result='failed')
    except Exception:
        payment.status = 'failed'
        payment.save(update_fields=['status', 'updated_at'])
        return redirect('pro_payment_result', result='failed')


@login_required
def razorpay_payment_status(request):
    payment = Payment.objects.filter(user=request.user).order_by('-created_at').first()
    if payment is None:
        return JsonResponse({'status': 'none', 'plan': None})
    return JsonResponse({
        'status': payment.status,
        'plan': payment.plan,
        'amount': float(payment.amount),
        'currency': payment.currency,
        'order_id': payment.razorpay_order_id,
        'payment_id': payment.razorpay_payment_id,
    })


@csrf_exempt
def razorpay_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    payload = request.body.decode('utf-8')
    signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')

    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return JsonResponse({'error': 'Webhook secret is not configured.'}, status=500)

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return JsonResponse({'error': 'Invalid webhook signature.'}, status=400)

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid payload.'}, status=400)

    payment_entity = event.get('payload', {}).get('payment', {}).get('entity', {})
    order_id = payment_entity.get('order_id') or event.get('payload', {}).get('order', {}).get('entity', {}).get('id')
    event_type = event.get('event')
    payment_id = payment_entity.get('id')

    if not order_id:
        return JsonResponse({'error': 'Missing order id in webhook payload.'}, status=400)

    payment = Payment.objects.filter(razorpay_order_id=order_id).first()
    if payment is None:
        return JsonResponse({'status': 'ignored', 'message': 'Unknown order id.'}, status=200)

    if payment.status == 'paid' and payment.razorpay_payment_id == payment_id:
        return JsonResponse({'status': 'duplicate'}, status=200)

    if event_type in {'payment.captured', 'order.paid'}:
        payment.status = 'paid'
        payment.razorpay_payment_id = payment_id or payment.razorpay_payment_id
        payment.paid_at = timezone.now()
        payment.save(update_fields=['status', 'razorpay_payment_id', 'paid_at', 'updated_at'])
        if payment.plan in {'PRO_MONTHLY', 'PRO_ANNUAL'}:
            _activate_membership(payment.user, payment.plan)
    elif event_type == 'payment.failed':
        payment.status = 'failed'
        payment.save(update_fields=['status', 'updated_at'])

    return JsonResponse({'status': 'received'})


@login_required
def pro_payment_result(request, result):
    if result not in {'success', 'failed', 'cancelled'}:
        return redirect('pro_landing')
    return render(request, 'pro/payment_result.html', {'result': result})


@login_required
def pro_feature(request, feature_slug):
    membership = _membership_for(request.user)
    features_info = {
        'resume-analyzer': {
            'name': 'AI Resume Analyzer',
            'desc': 'Upload your resume to get instant ATS scoring, detected technical skills, keyword coverage, and automated improvement suggestions.',
            'url_name': 'career_match',
            'action_label': 'Launch AI Resume Analyzer',
            'icon': 'bi-file-earmark-check',
        },
        'mock-interview': {
            'name': 'AI Mock Interview with Aria',
            'desc': 'Practice realistic video-call mock interviews with Aria, our AI interviewer. Get voice interaction, live observations, and instant feedback.',
            'url_name': 'ai_mock_interview',
            'action_label': 'Launch Live AI Interview with Aria',
            'icon': 'bi-camera-video',
        },
        'job-matching': {
            'name': 'Advanced Job Matching',
            'desc': 'AI-driven compatibility scores and personalized role recommendations matched against your verified skills and resume profile.',
            'url_name': 'career_match',
            'action_label': 'Explore Matched Roles & Companies',
            'icon': 'bi-bullseye',
        },
        'career-roadmap': {
            'name': 'Personal Career Roadmap',
            'desc': 'Explore your personalized skill gap analysis, target roles, and structured learning paths to maximize placement success.',
            'url_name': 'career_match',
            'action_label': 'View Career Roadmap & Skill Gap',
            'icon': 'bi-map',
        },
        'learning-hub': {
            'name': 'Premium Learning Hub',
            'desc': 'Exclusive interview preparation, DSA resources, system design tracks, and career enhancement courses.',
            'url_name': 'course_list',
            'action_label': 'Open Premium Learning Hub',
            'icon': 'bi-mortarboard',
        },
        'career-intelligence': {
            'name': 'Career Intelligence',
            'desc': 'Discover all jobs, market salary insights, skill demands, and companies you are currently eligible for based on your detected qualifications.',
            'url_name': 'career_match',
            'action_label': 'Explore AI Role Recommendations',
            'icon': 'bi-graph-up-arrow',
        },
    }
    feature_data = features_info.get(feature_slug, {
        'name': 'Premium AI Feature',
        'desc': 'Exclusive tools to boost your career preparation and recruiter visibility.',
        'url_name': 'career_match',
        'action_label': 'Access Premium Feature',
        'icon': 'bi-stars',
    })

    return render(request, 'pro/feature.html', {
        'membership': membership,
        'feature_name': feature_data['name'],
        'feature_desc': feature_data['desc'],
        'feature_url_name': feature_data['url_name'],
        'feature_action_label': feature_data['action_label'],
        'feature_icon': feature_data['icon'],
        'feature_slug': feature_slug,
    })


@login_required
def pro_cancel_subscription(request):
    """Handle subscription cancellation and turn off auto-renewal."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    membership = getattr(request.user, 'membership', None)
    if membership:
        membership.cancel_subscription()
        messages.info(request, 'Your PRO subscription auto-renewal has been cancelled.')
    return redirect('student_dashboard')


@login_required
def api_pro_status(request):
    """REST endpoint returning current user entitlement and expiry."""
    membership = getattr(request.user, 'membership', None)
    is_pro = bool(membership and membership.is_active)
    return JsonResponse({
        'is_pro': is_pro,
        'plan': request.user.plan,
        'status': membership.status if membership else 'FREE',
        'expiry_date': membership.current_period_end.isoformat() if (membership and membership.current_period_end) else None,
        'expiry_display': membership.current_period_end.strftime('%b %d, %Y') if (membership and membership.current_period_end) else None,
        'is_expiring_soon': membership.is_expiring_soon() if membership else False,
    })



def student_register_view(request):
    step = request.POST.get('step', 'account') if request.method == 'POST' else request.GET.get('step', 'account')
    pending_user_id = request.session.get('pending_student_registration')

    if step == 'profile' and pending_user_id:
        user = User.objects.filter(pk=pending_user_id, role='STUDENT').first()
        if user is None:
            request.session.pop('pending_student_registration', None)
            return redirect('student_register')
        profile = StudentProfile.objects.get_or_create(user=user)[0]
        profile_form = StudentProfileRegistrationForm(request.POST or None, request.FILES or None, instance=profile)
        if request.method == 'POST' and profile_form.is_valid():
            with transaction.atomic():
                profile_form.save()
            request.session.pop('pending_student_registration', None)
            login(request, user)
            messages.success(request, 'Welcome to CampusLink! Your student profile is ready. 🚀')
            return redirect('student_dashboard')
        return render(request, 'register.html', {
            'current_step': 'profile',
            'account_form': StudentAccountForm(),
            'profile_form': profile_form,
        })

    if request.method == 'POST' and 'step' not in request.POST:
        legacy_form = StudentRegistrationForm(request.POST, request.FILES)
        if legacy_form.is_valid():
            user = legacy_form.save()
            login(request, user)
            messages.success(request, 'Welcome to CampusLink! Your student profile is ready. 🚀')
            return redirect('student_dashboard')
        return render(request, 'register.html', {'current_step': 'account', 'account_form': legacy_form})

    account_form = StudentAccountForm(request.POST or None)
    if request.method == 'POST' and account_form.is_valid():
        user = account_form.create_user()
        request.session['pending_student_registration'] = user.pk
        return redirect(f'{reverse("student_register")}?step=profile')

    return render(request, 'register.html', {
        'current_step': 'account',
        'account_form': account_form,
    })


def home_view(request):
    membership = _membership_for(request.user) if request.user.is_authenticated else None
    is_pro = bool(membership and membership.is_active)
    profiles = list(StudentProfile.objects.all())
    average_completion = round(
        sum(profile.completion_percentage for profile in profiles) / len(profiles)
    ) if profiles else 0
    featured_jobs = Job.objects.order_by('-created_at')[:3]
    context = {
        'membership': membership,
        'is_pro': is_pro,
        'student_count': len(profiles),
        'company_count': Company.objects.count(),
        'job_count': Job.objects.count(),
        'application_count': Application.objects.count(),
        'average_completion': average_completion,
        'featured_jobs': featured_jobs,
        'features': [
            ('bi-search', 'Smart job discovery', 'Find relevant opportunities based on your skills and interests.'),
            ('bi-stars', 'AI career assistant', 'Get personalized guidance for your next career move.'),
            ('bi-file-earmark-check', 'Resume analyzer', 'Improve your resume with focused, actionable suggestions.'),
            ('bi-diagram-3', 'Skill gap analysis', 'Identify the capabilities required for your target role.'),
            ('bi-kanban', 'Application tracking', 'Track every application from Applied to Selected.'),
            ('bi-chat-square-text', 'Interview preparation', 'Practice role-specific questions with more confidence.'),
        ],
        'steps': [
            ('01', 'Build profile', 'Showcase your strengths, projects and ambitions.'),
            ('02', 'Discover opportunities', 'Explore roles aligned with your career direction.'),
            ('03', 'Apply & prepare', 'Track progress and close the most important skill gaps.'),
            ('04', 'Get hired', 'Move from campus talent to your next opportunity.'),
        ],
    }
    return render(request, 'home.html', context)

@login_required
def dashboard_redirect(request):
    return redirect(_dashboard_url(request.user))


@login_required
def profile_view(request):
    """Open the existing student profile or the account-backed profile for other roles."""
    if request.user.role == 'STUDENT':
        if request.method == 'POST':
            from students.views import student_profile
            return student_profile(request)
        return redirect('student_profile')

    recruiter_profile = getattr(request.user, 'recruiter_profile', None)
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save(update_fields=['first_name', 'last_name', 'email'])
        if recruiter_profile:
            recruiter_profile.designation = request.POST.get('designation', '').strip()
            recruiter_profile.phone = request.POST.get('phone', '').strip()
            recruiter_profile.save(update_fields=['designation', 'phone', 'updated_at'])
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    profile_values = [request.user.first_name, request.user.last_name, request.user.email]
    if recruiter_profile:
        profile_values.extend([
            recruiter_profile.designation,
            recruiter_profile.phone,
            recruiter_profile.company,
        ])
    profile_completion = round(sum(bool(value) for value in profile_values) / len(profile_values) * 100)

    if recruiter_profile:
        company_jobs = Job.objects.filter(company=recruiter_profile.company)
        stats = [
            ('bi-briefcase', 'Active jobs', company_jobs.count(), 'recruiter_job_create'),
            ('bi-people', 'Applications', Application.objects.filter(job__in=company_jobs).count(), 'recruiter_dashboard'),
            ('bi-calendar-check', 'Interviews', Application.objects.filter(job__in=company_jobs, status='INTERVIEW').count(), 'interview_list'),
        ]
        quick_actions = [
            ('recruiter_dashboard', 'Open recruiter dashboard', 'bi-speedometer2'),
            ('recruiter_job_create', 'Post a new job', 'bi-plus-circle'),
            ('interview_list', 'Review interviews', 'bi-camera-video'),
        ]
    else:
        stats = [
            ('bi-people', 'Students', StudentProfile.objects.count(), 'dashboard_redirect'),
            ('bi-building', 'Companies', Company.objects.count(), 'dashboard_redirect'),
            ('bi-briefcase', 'Open jobs', Job.objects.count(), 'job_list'),
        ]
        quick_actions = [
            ('dashboard_redirect', 'Open dashboard', 'bi-speedometer2'),
            ('job_list', 'Browse opportunities', 'bi-search'),
            ('notification_list', 'View notifications', 'bi-bell'),
        ]

    return render(request, 'account/profile.html', {
        'recruiter_profile': recruiter_profile,
        'profile_completion': profile_completion,
        'stats': stats,
        'quick_actions': quick_actions,
        'membership': _membership_for(request.user),
    })
