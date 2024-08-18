from django.urls import path
from .views import login_view, logout_view, order_view, payment_success, payment_cancel, register, previous_orders, submit_order

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('', order_view, name='order'),
    path('success/', payment_success, name='payment_success'),
    path('cancel/', payment_cancel, name='payment_cancel'),
    path('previous_orders/', previous_orders, name='previous_orders'),
    path('logout/', logout_view, name='logout'),
    path('submit_order/', submit_order, name='submit_order'),  # Changed path
]
