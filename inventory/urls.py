from django.urls import path

from inventory import views

app_name = 'inventory'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_create, name='product_create'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('restock/', views.stock_onboarding_build, name='stock_onboarding_build'),
    path('restock/cart/add/', views.stock_onboarding_cart_add, name='stock_onboarding_cart_add'),
    path('restock/cart/remove/<int:pk>/', views.stock_onboarding_cart_remove, name='stock_onboarding_cart_remove'),
    path('restock/submit/', views.stock_onboarding_submit, name='stock_onboarding_submit'),
    path('restock/queue/', views.stock_onboarding_queue, name='stock_onboarding_queue'),
    path('restock/<int:pk>/approve/', views.stock_onboarding_approve, name='stock_onboarding_approve'),
    path('restock/<int:pk>/reject/', views.stock_onboarding_reject, name='stock_onboarding_reject'),
]
