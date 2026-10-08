from django.urls import path
from . import views

urlpatterns = [
    path('', views.company_list, name='company_list'),
    path('<int:company_id>/', views.company_detail, name='company_detail'),
    path('<int:company_id>/connect/', views.connect_company, name='connect_company'),
]
