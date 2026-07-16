from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_create, name='user_create'),
    path('employee-requests/', views.role_request_queue, name='role_request_queue'),
    path('employee-requests/<int:pk>/approve/', views.role_request_approve, name='role_request_approve'),
    path('employee-requests/<int:pk>/reject/', views.role_request_reject, name='role_request_reject'),
]
