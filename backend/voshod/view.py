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

    # Получаем данные из запроса
    data = request.data
    print(f"Received payment data: {data}")

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
            # Используем правильные имена полей, соответствующие фронтенду
            customer_name = data.get('customer_name', '')
            customer_email = data.get('customer_email', '')
            customer_phone = data.get('customer_phone', '')
            customer_address = data.get('delivery_address', '')
            postal_code = ''

            # Если есть нормализованный адрес, используем данные из него
            normalized_address = data.get('normalized_address', {})
            if normalized_address:
                # Если есть индекс в нормализованном адресе, используем его
                if normalized_address.get('index'):
                    postal_code = normalized_address.get('index')

            # Создаем заказ с адресом и индексом
            order = Order.objects.create(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                customer_address=customer_address,
                postal_code=postal_code,
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
    Нормализация адреса через API Почты России
    """
    try:
        # Логируем входящий запрос
        logger.debug("=== START normalize_address ===")
        logger.debug(f"Request data: {request.data}")

        address = request.data.get('address')
        if not address:
            return JsonResponse({
                'status': 'error',
                'message': 'Address is required'
            }, status=400)

        # Вызываем API Почты России
        result = pochta_api.normalize_address(address)

        if isinstance(result, dict) and 'error' in result:
            return JsonResponse({
                'status': 'error',
                'message': result['error']
            }, status=400)

        # Проверяем качество нормализации
        quality_code = result.get('quality-code', '')
        quality_description = get_quality_description(quality_code)

        # Формируем ответ
        normalized_address = {
            'index': result.get('index', ''),
            'region': result.get('region', ''),
            'area': result.get('area', ''),
            'place': result.get('place', ''),
            'location': result.get('location', ''),  # Важно включить поле location
            'street': result.get('street', ''),
            'house': result.get('house', ''),
            'building': result.get('building', ''),
            'corpus': result.get('corpus', ''),
            'letter': result.get('letter', ''),
            'office': result.get('office', ''),
            'vladenie': result.get('vladenie', ''),
            'room': result.get('room', '')
        }

        return JsonResponse({
            'status': 'success',
            'message': 'Address normalized',
            'is_valid': quality_code in ['GOOD', 'POSTAL_BOX', 'ON_DEMAND', 'UNDEF_05'],
            'normalized_address': normalized_address,
            'quality': {
                'code': quality_code,
                'description': quality_description
            }
        })
    except Exception as e:
        logger.error(f"Exception in normalize_address: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def get_quality_description(quality_code):
    quality_descriptions = {
        'GOOD': 'Адрес распознан уверенно',
        'POSTAL_BOX': 'Почтовый ящик',
        'ON_DEMAND': 'До востребования',
        'UNDEF_05': 'Абонентский ящик',
        'UNDEF_06': 'Войсковая часть',
        'ACCURATE': 'Адрес распознан с предупреждениями',
        'OVERREFINED': 'Адрес распознан с уточнением',
        'CONFIRMED_MANUALLY': 'Адрес подтвержден вручную',
        'FOREIGN_ADDRESS': 'Иностранный адрес',
        'NOT_VALIDATED': 'Адрес не удалось распознать'
    }
    return quality_descriptions.get(quality_code, 'Неизвестный код качества')


@api_view(['GET'])
def address_suggestions(request):
    """
    Получение подсказок адресов
    """
    try:
        query = request.GET.get('query', '')
        if len(query) < 3:
            return JsonResponse({
                'status': 'error',
                'message': 'Query must be at least 3 characters long',
                'suggestions': []
            })

        # Вызываем API Почты России
        result = pochta_api.normalize_address(query)
        if isinstance(result, dict) and 'error' in result:
            return JsonResponse({
                'status': 'error',
                'message': result['error'],
                'suggestions': []
            })

        # Формируем подсказку на основе нормализованного адреса
        formatted_address = []
        if result.get('index'):
            formatted_address.append(result['index'])
        if result.get('region'):
            formatted_address.append(result['region'])
        if result.get('place') and result.get('place') != result.get('region'):
            formatted_address.append(result['place'])
        # Добавляем location (микрорайон)
        if result.get('location'):
            formatted_address.append(result['location'])
        if result.get('street'):
            formatted_address.append(result['street'])
        if result.get('house'):
            formatted_address.append(result['house'])

        suggestion_text = ', '.join(formatted_address)

        suggestions = [{
            'text': suggestion_text,
            'value': suggestion_text,
            'original': result
        }]

        return JsonResponse({
            'status': 'success',
            'suggestions': suggestions
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'suggestions': []
        })

from .cdek_api import CDEKApi


@api_view(['POST'])
def calculate_cdek_shipping(request):
    """
    Расчет стоимости доставки через API CDEK
    """
    try:
        logger.debug("=== START calculate_cdek_shipping ===")
        logger.debug(f"Request data: {request.data}")

        # Получаем данные из запроса
        index_to = request.data.get('index_to')

        # Проверяем обязательные параметры
        if not index_to:
            return JsonResponse({
                'status': 'error',
                'message': 'Recipient index is required'
            }, status=400)

        # Получаем вес корзины
        # Вместо вызова get_cart_weight напрямую, получаем вес другим способом
        # Вариант 1: Получаем вес из запроса, если он передан
        weight = request.data.get('mass')

        # Вариант 2: Если вес не передан, делаем отдельный запрос к API для получения веса
        if not weight:
            # Создаем новый HttpRequest для вызова get_cart_weight
            from django.http import HttpRequest
            from django.contrib.sessions.middleware import SessionMiddleware

            # Создаем новый HttpRequest
            http_request = HttpRequest()

            # Копируем сессию из оригинального запроса
            http_request.session = request.session

            # Получаем ответ от функции get_cart_weight
            weight_response = get_cart_weight(http_request)

            # Парсим JSON-ответ для получения веса
            import json
            weight_data = json.loads(weight_response.content)

            if weight_data.get('status') == 'success':
                weight = weight_data.get('total_weight', 0)
            else:
                weight = 0

        # Если вес равен 0, устанавливаем минимальное значение
        if not weight or weight == 0:
            weight = 0.1

        # Преобразуем вес из кг в граммы для API CDEK
        weight_grams = int(float(weight) * 1000)

        logger.debug(f"Weight: {weight} kg, {weight_grams} g")

        # Инициализируем API CDEK
        cdek_api = CDEKApi(
            client_id=settings.CDEK_CLIENT_ID,
            client_secret=settings.CDEK_CLIENT_SECRET,
            base_url=settings.CDEK_API_URL
        )

        # Вызываем API CDEK
        result = cdek_api.calculate_shipping(
            postal_code=index_to,
            weight=weight_grams
        )

        logger.debug(f"CDEK API result: {result}")

        if 'error' in result:
            return JsonResponse({
                'status': 'error',
                'message': result['error']
            }, status=400)

        # Получаем стоимость доставки
        shipping_cost = result.get('shipping_cost')

        # Формируем ответ
        response_data = {
            'status': 'success',
            'shipping_cost': shipping_cost
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error calculating CDEK shipping: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['POST'])
def calculate_shipping_cost(request):
    """
    Расчет стоимости доставки через API Почты России
    """
    try:
        logger.debug("=== START calculate_shipping_cost ===")
        logger.debug(f"Request data: {request.data}")

        # Получаем данные из запроса
        index_to = request.data.get('index_to')
        mass = request.data.get('mass')

        # Проверяем обязательные параметры
        if not index_to:
            return JsonResponse({
                'status': 'error',
                'message': 'Recipient index is required'
            }, status=400)

        if not mass:
            return JsonResponse({
                'status': 'error',
                'message': 'Package mass is required'
            }, status=400)

        # Опциональные параметры
        height = request.data.get('height', 2)
        length = request.data.get('length', 5)
        width = request.data.get('width', 197)
        mail_category = request.data.get('mail_category', 'ORDINARY')
        mail_type = request.data.get('mail_type', 'POSTAL_PARCEL')
        fragile = request.data.get('fragile', True)

        # Вызываем API Почты России
        result = pochta_api.calculate_shipping(
            index_to=index_to,
            mass=mass,
            height=height,
            length=length,
            width=width,
            mail_category=mail_category,
            mail_type=mail_type,
            fragile=fragile
        )

        logger.debug(f"API result: {result}")

        if isinstance(result, dict) and 'error' in result:
            return JsonResponse({
                'status': 'error',
                'message': result['error']
            }, status=400)

        # Проверяем, есть ли в ответе поле cost_in_rubles, которое мы добавили в pochta_api.py
        shipping_cost = result.get('cost_in_rubles', 300)

        # Также извлекаем информацию о сроках доставки, если она есть
        delivery_time = None
        if 'delivery-time' in result:
            delivery_time = {
                'min_days': result['delivery-time'].get('min-days', 0),
                'max_days': result['delivery-time'].get('max-days', 0)
            }

        # Формируем ответ
        response_data = {
            'status': 'success',
            'shipping_cost': shipping_cost
        }

        # Добавляем информацию о сроках доставки, если она есть
        if delivery_time:
            response_data['delivery_time'] = delivery_time

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error in calculate_shipping_cost: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }, status=500)