# apps/orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Buyurtma jarayoni
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('confirm/<int:order_id>/', views.OrderConfirmView.as_view(), name='order_confirm'),
    path('payment/<int:order_id>/', views.PaymentView.as_view(), name='payment'),
    path('success/<int:order_id>/', views.OrderSuccessView.as_view(), name='order_success'),

    # Buyurtmalar ro'yxati
    path('', views.OrderListView.as_view(), name='order_list'),

    # Buyurtma tafsilotlari
    path('<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<str:order_number>/status/', views.OrderStatusView.as_view(), name='order_status'),
    path('<str:order_number>/invoice/', views.OrderInvoiceView.as_view(), name='order_invoice'),

    # Buyurtmani bekor qilish (AJAX)
    path('<str:order_number>/cancel/', views.OrderCancelView.as_view(), name='order_cancel'),

    # Anonim buyurtma kuzatuvi
    path('track/', views.OrderTrackingView.as_view(), name='order_tracking'),
]