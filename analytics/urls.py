
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.officer_dashboard, name='officer_dashboard'),
    path('companies/<int:company_id>/verify/', views.verify_company, name='verify_company'),
]
