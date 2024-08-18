import json  # Add this import statement

from django.http import JsonResponse
import stripe
from .models import Order, OrderItem, Dish
from .forms import RegistrationForm
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm

stripe.api_key = settings.STRIPE_SECRET_KEY

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('order')
    else:
        form = RegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('order')
    else:
        form = AuthenticationForm()
    return render(request, 'orders/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def order_view(request):
    if request.method == 'POST':
        order = Order(customer=request.user)
        order.save()
        total_amount = 0
        line_items = []
        
        for dish_id, quantity in zip(request.POST.getlist('dishes[]'),
                                     request.POST.getlist('quantities[]')):
            dish_id = int(dish_id)
            quantity = int(quantity)
            dish = Dish.objects.get(pk=dish_id)
            order_item = OrderItem(order=order, dish=dish, quantity=quantity)
            order_item.save()
            total_amount += dish.price * quantity
            
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': dish.name,
                        'images': [request.build_absolute_uri(dish.image.url)],
                    },
                    'unit_amount': int(dish.price * 100),
                },
                'quantity': quantity,
            })
        
        order.total_amount = total_amount
        order.save()

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
            customer_email=request.user.email,
        )

        return redirect(session.url, code=303)

    dishes = []
    for dish in Dish.objects.all():
        dishes.append({
            'id': dish.id,
            'name': dish.name,
            'price': dish.price,
            'image': dish.image.url,
            'available': dish.available
        })
    return render(request, 'orders/order.html', {'dishes': tuple(dishes)})

def payment_success(request):
    return render(request, 'orders/payment_success.html')

def payment_cancel(request):
    return render(request, 'orders/payment_cancel.html')

@login_required
def previous_orders(request):
    orders = Order.objects.filter(customer=request.user).all()
    orders_list = []
    for order in orders:
        order_items = OrderItem.objects.filter(order=order).all()
        orders_list.append({
            'order':order,
            'items':order_items
        })
    return render(request, 'orders/previous_order.html', {'list':tuple(orders_list)})

@login_required
def submit_order(request):
    if request.method == 'POST':
        cart_items = request.POST.get('cart_items', '[]')
        cart_items = json.loads(cart_items)  # Use json.loads here

        order = Order(customer=request.user)
        order.save()
        total_amount = 0
        line_items = []

        for item in cart_items:
            dish_id = item['id']
            quantity = item['quantity']
            dish = Dish.objects.get(pk=dish_id)
            order_item = OrderItem(order=order, dish=dish, quantity=quantity)
            order_item.save()
            total_amount += dish.price * quantity

            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': dish.name,
                        'images': [request.build_absolute_uri(dish.image.url)],
                    },
                    'unit_amount': int(dish.price * 100),
                },
                'quantity': quantity,
            })

        order.total_amount = total_amount
        order.save()

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
            customer_email=request.user.email,
        )

        return JsonResponse({'session_url': session.url})

    return JsonResponse({'error': 'Invalid request'}, status=400)
