from django.urls import path

from inventory import views

app_name = 'inventory'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_create, name='product_create'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('restock/', views.stock_onboarding_create, name='stock_onboarding_create'),
    path('restock/queue/', views.stock_onboarding_queue, name='stock_onboarding_queue'),
    path('restock/<int:pk>/approve/', views.stock_onboarding_approve, name='stock_onboarding_approve'),
    path('restock/<int:pk>/reject/', views.stock_onboarding_reject, name='stock_onboarding_reject'),
]
