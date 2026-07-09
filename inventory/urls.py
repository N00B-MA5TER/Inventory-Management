from django.urls import path

from inventory import views

app_name = 'inventory'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_create, name='product_create'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
]
