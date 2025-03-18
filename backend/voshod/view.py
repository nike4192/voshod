from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.db import transaction
import logging
import traceback
import json
from django.http import JsonResponse
from .pochta_api import PochtaAPI
from django.conf import settings
from rest_framework.decorators import api_view
from .models import Product, Order, OrderItem
from .serializers import ProductSerializer


@require_GET
@csrf_exempt  # Отключаем CSRF-проверку для этого view
def get_csrf_token(request):
    """
    Устанавливает и возвращает CSRF-токен для клиента с явным контролем над cookie.
    """
    # Получаем CSRF-токен
    csrf_token = get_token(request)

    # Создаем ответ
    response = JsonResponse({
        'csrfToken': csrf_token,
        'status': 'success',
        'message': 'CSRF token has been set in cookies'
    })

    # Явно устанавливаем CSRF cookie с нужными параметрами
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,  # По умолчанию 'csrftoken'
        value=csrf_token,
        max_age=settings.CSRF_COOKIE_AGE,  # По умолчанию 1 год
        domain=settings.CSRF_COOKIE_DOMAIN,  # Домен cookie
        path=settings.CSRF_COOKIE_PATH,  # Путь cookie, обычно '/'
        secure=settings.CSRF_COOKIE_SECURE,  # True для HTTPS
        httponly=settings.CSRF_COOKIE_HTTPONLY,  # Обычно False для CSRF
        samesite=settings.CSRF_COOKIE_SAMESITE  # 'Lax', 'Strict' или 'None'
    )

    return response

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

    # Подсчитываем общее количество товаров
    total_quantity = 0
    for item_data in cart.values():
        total_quantity += item_data['quantity']

    return JsonResponse({
        'cart': cart,
        'total_quantity': total_quantity
    })

@api_view(['GET'])
def get_cart_products(request):
    cart = request.session.get('cart', {})
    cart_products = []
    total_price = 0
    total_quantity = 0

    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            quantity = item_data['quantity']
            total_quantity += quantity
            item_price = product.price * quantity
            total_price += item_price

            # Формируем URL изображения, если оно есть
            image_url = None
            if product.image:
                # Используйте абсолютный URL для изображения
                image_url = request.build_absolute_uri(product.image.url)

            cart_products.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,  # Добавлено из второй версии
                'price': product.price,
                'quantity': quantity,
                'image_url': image_url,
                'total': item_price,
                'item_total': item_price  # Добавлено для совместимости со второй версией
            })
        except Product.DoesNotExist:
            # Удаляем товар из корзины, если он не найден
            del cart[product_id]
            request.session.modified = True

    return JsonResponse({
        'status': 'success',  # Добавлено из второй версии
        'cart_products': cart_products,
        'total_price': total_price,
        'total_quantity': total_quantity
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


@api_view(['GET'])
def get_cart_weight(request):
    cart = request.session.get('cart', {})
    total_weight = 0

    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            # Проверяем формат данных в корзине
            if isinstance(item_data, dict) and 'quantity' in item_data:
                quantity = item_data['quantity']
            else:
                quantity = item_data  # Если quantity хранится напрямую

            # Умножаем вес товара на его количество в корзине
            total_weight += float(product.weight) * quantity
        except Product.DoesNotExist:
            # Пропускаем товары, которых нет в базе данных
            continue
        except Exception as e:
            print(f"Ошибка при расчете веса для товара {product_id}: {str(e)}")

    return JsonResponse({
        'status': 'success',
        'total_weight': total_weight
    })
# ads
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.conf import settings
from .pochta_api import PochtaAPI
import logging

logger = logging.getLogger(__name__)

# Инициализация API Почты России
pochta_api = PochtaAPI(
    token=settings.POCHTA_API_TOKEN,
    key=settings.POCHTA_API_KEY
)


@api_view(['POST'])
def normalize_address(request):
    """
    Нормализация адреса с использованием API Почты России
    """
    try:
        logger.debug("=== START normalize_address ===")
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"Request data: {request.data}")

        # Получаем адрес из тела запроса
        address = request.data.get('address', '')

        if not address:
            logger.debug("Address is empty")
            return JsonResponse({
                'status': 'error',
                'message': 'Адрес не указан'
            }, status=400)

        logger.debug(f"Processing address: {address}")

        # Вызываем API для нормализации адреса
        result = pochta_api.normalize_address(address)
        logger.debug(f"API result: {result}")

        if not result:
            logger.debug("Empty result from API")
            return JsonResponse({
                'status': 'error',
                'message': 'Не удалось нормализовать адрес'
            }, status=400)

        # Проверяем результат нормализации
        is_valid, message = pochta_api.validate_address(result)
        logger.debug(f"Validation result: valid={is_valid}, message={message}")

        if not is_valid:
            logger.debug("Address validation failed")
            return JsonResponse({
                'status': 'error',
                'message': message
            }, status=400)

        # Получаем нормализованный адрес
        normalized_address = result.get('normalized-address', {})
        quality_code = result.get('quality-code', '')

        # Форматируем адрес для отображения
        formatted_address = ', '.join(filter(None, [
            normalized_address.get('index', ''),
            normalized_address.get('region', ''),
            normalized_address.get('area', ''),
            normalized_address.get('place', ''),
            normalized_address.get('street', ''),
            normalized_address.get('house', '')
        ]))

        logger.debug(f"Formatted address: {formatted_address}")
        logger.debug("=== END normalize_address ===")

        # Возвращаем успешный результат
        return JsonResponse({
            'status': 'success',
            'message': message,
            'normalized_address': normalized_address,
            'formatted_address': formatted_address,
            'quality_code': quality_code,
            'quality_description': message
        })
    except Exception as e:
        logger.error(f"Error in normalize_address: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при нормализации адреса: {str(e)}'
        }, status=500)

@api_view(['POST'])
def address_suggestions(request):
    """
    Получение подсказок адресов для автозаполнения
    """
    try:
        logger.debug("=== START address_suggestions ===")
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"Request data: {request.data}")

        # Получаем запрос из тела запроса
        query = request.data.get('query', '')

        if not query or len(query) < 3:
            logger.debug("Query is too short")
            return JsonResponse({
                'status': 'error',
                'message': 'Запрос должен содержать не менее 3 символов',
                'suggestions': []
            })

        logger.debug(f"Processing query: {query}")

        # Вызываем API для получения вариантов адресов
        try:
            # Здесь мы используем API нормализации адреса, но в реальном сценарии
            # вы можете использовать специальный API для подсказок адресов
            # Отправляем несколько вариаций запроса для получения разных результатов
            variations = [
                query,
                f"{query}, ул.",
                f"{query}, пр.",
                f"{query}, д."
            ]

            suggestions = []

            for variation in variations:
                result = pochta_api.normalize_address(variation)

                if result and isinstance(result, list) and len(result) > 0:
                    # Если API вернуло список результатов
                    for item in result:
                        if 'original-address' in item and 'address-normalized' in item:
                            # Форматируем адрес для отображения
                            normalized = item['address-normalized']
                            formatted_address = ', '.join(filter(None, [
                                normalized.get('index', ''),
                                normalized.get('region', ''),
                                normalized.get('area', ''),
                                normalized.get('place', ''),
                                normalized.get('street', ''),
                                normalized.get('house', '')
                            ]))

                            suggestions.append({
                                'text': formatted_address,
                                'value': formatted_address,
                                'original': normalized
                            })
                elif result and isinstance(result, dict) and 'normalized-address' in result:
                    # Если API вернуло один результат
                    normalized = result['normalized-address']
                    formatted_address = ', '.join(filter(None, [
                        normalized.get('index', ''),
                        normalized.get('region', ''),
                        normalized.get('area', ''),
                        normalized.get('place', ''),
                        normalized.get('street', ''),
                        normalized.get('house', '')
                    ]))

                    suggestions.append({
                        'text': formatted_address,
                        'value': formatted_address,
                        'original': normalized
                    })

            # Удаляем дубликаты по полю 'value'
            unique_suggestions = []
            seen_values = set()

            for suggestion in suggestions:
                if suggestion['value'] not in seen_values:
                    seen_values.add(suggestion['value'])
                    unique_suggestions.append(suggestion)

            # Если не удалось получить подсказки, добавляем исходный запрос
            if not unique_suggestions:
                unique_suggestions.append({
                    'text': query,
                    'value': query
                })

            logger.debug(f"Generated {len(unique_suggestions)} unique suggestions")

            return JsonResponse({
                'status': 'success',
                'suggestions': unique_suggestions[:5]  # Ограничиваем количество подсказок
            })
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            logger.error(traceback.format_exc())

            # В случае ошибки возвращаем хотя бы исходный запрос
            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка при получении подсказок: {str(e)}',
                'suggestions': [{'text': query, 'value': query}]
            })
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Неожиданная ошибка: {str(e)}',
            'suggestions': []
        })