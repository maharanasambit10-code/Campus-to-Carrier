
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.views.static import serve
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from accounts.views import (
    admin_dashboard,
    admin_export_data_report,
    admin_login_view,
    admin_send_announcement,
    admin_toggle_maintenance,
    dashboard_redirect,
    home_view,
    login_view,
    profile_view,
    pro_cancel_subscription,
    pro_checkout,
    pro_feature,
    pro_landing,
    pro_payment_result,
    api_pro_status,
    phonepe_create_order,
    phonepe_payment_callback,
    razorpay_create_order,
    razorpay_payment_status,
    razorpay_verify_payment,
    razorpay_webhook,
    student_register_view,
)

urlpatterns = [
    path('admin/login/', admin_login_view, name='admin_login'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/dashboard/announcement/', admin_send_announcement, name='admin_send_announcement'),
    path('admin/dashboard/export-report/', admin_export_data_report, name='admin_export_data_report'),
    path('admin/dashboard/maintenance/', admin_toggle_maintenance, name='admin_toggle_maintenance'),
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', student_register_view, name='student_register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
    path('profile/', profile_view, name='profile'),
    path('pro/', pro_landing, name='pro_landing'),
    path('premium/', pro_landing, name='premium'),
    path('pro/checkout/', pro_checkout, name='pro_checkout'),
    path('pro/subscription/cancel/', pro_cancel_subscription, name='pro_cancel_subscription'),
    path('pro/feature/<slug:feature_slug>/', pro_feature, name='pro_feature'),
    path('pro/payment/<str:result>/', pro_payment_result, name='pro_payment_result'),
    path('api/pro/status/', api_pro_status, name='api_pro_status'),
    path('api/payment/create-order/', phonepe_create_order, name='api_razorpay_create_order'), # Kept name for frontend compatibility if needed, though we will update it
    path('api/payment/phonepe/create-order/', phonepe_create_order, name='api_phonepe_create_order'),
    path('api/payment/phonepe/callback/', phonepe_payment_callback, name='api_phonepe_callback'),
    path('api/payment/verify/', razorpay_verify_payment, name='api_razorpay_verify_payment'),
    path('api/payment/status/', razorpay_payment_status, name='api_razorpay_payment_status'),
    path('api/payment/webhook/', razorpay_webhook, name='api_razorpay_webhook'),
    path('payments/razorpay/create-order/', razorpay_create_order, name='razorpay_create_order'),
    path('payments/razorpay/verify/', razorpay_verify_payment, name='razorpay_verify_payment'),
    path('payments/razorpay/webhook/', razorpay_webhook, name='razorpay_webhook'),
    path('student/', include('students.urls')),
    path('officer/', include('analytics.urls')),
    path('jobs/', include('jobs.urls')),
    path('recruiter/', include('recruiters.urls')),
    path('notifications/', include('notifications.urls')),
    path('interviews/', include('interviews.urls')),
    path('courses/', include('courses.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
