from django.urls import path

from billing import views

app_name = 'billing'

urlpatterns = [
    path('orders/new/', views.order_build, name='order_build'),
    path('orders/cart/add/<int:pk>/', views.cart_add, name='cart_add'),
    path('orders/cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('orders/place/', views.order_place, name='order_place'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/bill/new/', views.bill_create, name='bill_create'),
    path('bills/<int:pk>/', views.bill_detail, name='bill_detail'),
    path('summary/daily/', views.daily_summary, name='daily_summary'),
    path('summary/monthly/', views.monthly_summary, name='monthly_summary'),
]
