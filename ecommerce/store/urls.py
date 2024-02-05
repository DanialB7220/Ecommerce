from django.urls import path
from .import views 
from.views import *

urlpatterns = [
    path('', views.store, name="store"),
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),
    
    path('update_item/', views.updateItem, name="update_item"),
    path('process_order/', views.processOrder, name="process_order"),
    path('create-payment-intent/', create_payment_intent, name='create_payment_intent'),
    path('stripe-webhook/', stripe_webhook, name='stripe_webhook'),

]
