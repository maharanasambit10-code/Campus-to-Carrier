from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse


def _user_dashboard_url(user):
    if user.role == 'STUDENT':
        return reverse('student_dashboard')
    if user.role == 'RECRUITER':
        return reverse('recruiter_dashboard')
    if user.role in {'PLACEMENT_OFFICER', 'SUPER_ADMIN'}:
        return reverse('officer_dashboard')
    return reverse('home')


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.role not in roles:
                return redirect(_user_dashboard_url(request.user))
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def pro_required(view_func):
    """Enforces active PRO membership on views with API/AJAX 403 fallback."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        membership = getattr(request.user, 'membership', None)
        is_pro = bool(membership and membership.is_active)
        if not is_pro:
            is_ajax_or_api = (
                request.headers.get('x-requested-with') == 'XMLHttpRequest'
                or request.path.startswith('/api/')
                or request.content_type == 'application/json'
            )
            if is_ajax_or_api:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'PRO_REQUIRED',
                    'message': 'This feature requires an active CampusLink PRO membership.',
                    'upgrade_url': reverse('pro_checkout'),
                    'price': '₹1/month',
                }, status=403)

            from django.contrib import messages
            messages.warning(
                request,
                'This feature requires an active CampusLink PRO membership. Upgrade for only ₹1 to unlock full access!'
            )
            return redirect('pro_checkout')
        return view_func(request, *args, **kwargs)

    return wrapped_view


try:
    from rest_framework.permissions import BasePermission

    class IsProMember(BasePermission):
        """DRF Permission requiring active PRO membership."""
        message = 'CampusLink PRO membership is required to access this resource.'

        def has_permission(self, request, view):
            return bool(
                request.user
                and request.user.is_authenticated
                and getattr(request.user, 'is_pro', False)
            )
except ImportError:
    pass