from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Product
from rest_framework.decorators import api_view
from .models import Product, Order, OrderItem
from .serializers import ProductSerializer
from django.db import transaction


@api_view(['POST'])
def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    # Проверяем, существует ли товар в корзине
    if str(product.pk) in cart:
        # Если существует, увеличиваем количество
        cart[str(product.pk)]['quantity'] += 1
    else:
        # Если не существует, добавляем товар с количеством 1
        cart[str(product.pk)] = {'quantity': 1}

    # Сохраняем обновленную корзину в сессии
    request.session['cart'] = cart
    request.session.modified = True  # Явно помечаем сессию как измененную

    return JsonResponse({'status': 'success', 'cart': cart})


@api_view(['GET'])
def get_cart(request):
    cart = request.session.get('cart', {})
    return JsonResponse({'cart': cart})


@api_view(['GET'])
def get_cart_products(request):
    cart = request.session.get('cart', {})

    # Создаем список товаров в корзине
    cart_products = []
    total_price = 0  # Инициализируем общую стоимость

    for product_id, item in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            item_price = product.price * item['quantity']  # Рассчитываем стоимость для данного товара
            total_price += item_price  # Добавляем к общей стоимости

            # Формируем URL изображения, если оно есть
            image_url = None
            if product.image:
                image_url = request.build_absolute_uri(product.image.url)

            cart_products.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'quantity': item['quantity'],
                'item_total': item_price,
                'image_url': image_url,
            })
        except Product.DoesNotExist:
            # Если товар не найден, пропускаем его
            continue

    return JsonResponse({
        'status': 'success',
        'cart_products': cart_products,
        'total_price': total_price
    })


@api_view(['DELETE'])
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    # Проверяем, существует ли товар в корзине
    if str(product_id) in cart:
        # Удаляем товар из корзины
        del cart[str(product_id)]

        # Сохраняем обновленную корзину в сессии
        request.session['cart'] = cart
        request.session.modified = True  # Явно помечаем сессию как измененную

        return JsonResponse({'status': 'success', 'message': 'Товар удален из корзины', 'cart': cart})
    else:
        return JsonResponse({'status': 'error', 'message': 'Товар не найден в корзине'}, status=404)


@api_view(['POST'])
def process_payment(request):
    cart = request.session.get('cart', {})

    if not cart:
        return JsonResponse({'status': 'error', 'message': 'Корзина пуста'}, status=400)

    # Отладочная информация
    print(f"Cart contents: {cart}")

    # Проверяем наличие товаров на складе
    insufficient_stock = []

    for product_id, item in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            print(f"Product {product.id}: stock={product.stock}, quantity={item['quantity']}")
            if product.stock < item['quantity']:
                insufficient_stock.append({
                    'id': product.id,
                    'name': product.name,
                    'available': product.stock,
                    'requested': item['quantity']
                })
        except Product.DoesNotExist:
            print(f"Product with ID {product_id} not found")
            return JsonResponse({'status': 'error', 'message': f'Товар с ID {product_id} не найден'}, status=404)
        except Exception as e:
            print(f"Error checking product {product_id}: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # Если есть товары с недостаточным количеством на складе
    if insufficient_stock:
        return JsonResponse({
            'status': 'error',
            'message': 'Недостаточно товаров на складе',
            'insufficient_items': insufficient_stock
        }, status=400)

    # Если все товары доступны, обрабатываем заказ
    try:
        with transaction.atomic():  # Используем транзакцию для обеспечения целостности данных
            # Создаем заказ
            total_price = 0
            for product_id, item in cart.items():
                product = Product.objects.get(id=product_id)
                total_price += product.price * item['quantity']

            # Получаем данные пользователя из запроса
            customer_name = request.data.get('customer_name', 'Гость')
            customer_email = request.data.get('customer_email', '')
            customer_phone = request.data.get('customer_phone', '')

            print(
                f"Creating order: name={customer_name}, email={customer_email}, phone={customer_phone}, total={total_price}")

            # Создаем заказ
            order = Order.objects.create(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                total_price=total_price,
                status='pending'
            )

            print(f"Order created with ID: {order.id}")

            # Создаем элементы заказа и обновляем stock
            for product_id, item in cart.items():
                product = Product.objects.get(id=product_id)

                print(f"Creating order item: product={product.id}, quantity={item['quantity']}")

                # Создаем элемент заказа
                OrderItem.objects.create(
                    order=order,
                    merch=product,
                    quantity=item['quantity']
                )

                # Обновляем количество товара на складе
                product.stock -= item['quantity']
                product.save()

                print(f"Updated product stock: {product.id} now has {product.stock} items")

            # Очищаем корзину
            request.session['cart'] = {}
            request.session.modified = True

            return JsonResponse({
                'status': 'success',
                'message': 'Заказ успешно оформлен',
                'order_id': order.id
            })

    except Exception as e:
        print(f"Error processing payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)