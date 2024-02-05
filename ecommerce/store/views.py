from django.shortcuts import render
import json
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
import datetime
import stripe


from .models import *
from .utils import cookieCart,cartData,guestOrder
from .models import Payment

# Create your views here.

def store(request):
    
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
        
    products = Product.objects.all()
    context = {'products':products, 'cartItems':cartItems}
    return render(request, 'store/store.html', context)

def cart(request):
    data = cartData(request)
    
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    context = {'items':items, 'order':order,'cartItems':cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request): 
    data = cartData(request)
    
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
        
    context = {'items':items, 'order':order, 'cartItems':cartItems, 'stripe_key': ' '}
    return render(request, 'store/checkout.html', context)






def updateItem(request):
        data = json.loads(request.body)
        productId = data['productId']
        action = data['action']
        
        print('Action:', action)
        print('Product:', productId)

        customer = request.user.customer
        product = Product.objects.get(id=productId)
        order, created = Order.objects.get_or_create(customer=customer, complete=False)


        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
        
        if action == 'add':
            orderItem.quantity = (orderItem.quantity + 1)
            
        elif action == 'remove':
            orderItem.quantity = (orderItem.quantity - 1)
            
        orderItem.save()
        
        if orderItem.quantity <= 0:
            orderItem.delete()
            
        return JsonResponse('Item was added', safe=False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete = False)
        
    else:
        customer, order = guestOrder(request, data)
            
    total = float(data['form']['total'])
    order.transaction_id = transaction_id
        
    if total == order.get_cart_total:
        order.complete = True
        # order.stripe_charge_id = charge.id
        # Charge the c  ustomer's card
    order.save()
    
    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )
    
    return JsonResponse('Payment Complete!', safe=False)


stripe.api_key = ' '

def create_payment_intent(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount),
            currency='usd',
        )

        Payment.objects.create(
            amount=amount,
            description=description,
            stripe_payment_intent_id=payment_intent.id
        )

        return JsonResponse({'clientSecret': payment_intent.client_secret})
    else:
        return render(request, 'payment_form.html')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, 'your_stripe_endpoint_secret'
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        # Payment succeeded, update your database or perform other actions
        payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
        print('PaymentIntent was successful!')

    # Other event types can be handled similarly

    return HttpResponse(status=200)



