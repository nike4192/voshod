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
from .yookassa_api import YooKassaAPI
from .pochta_api import PochtaAPI



logger = logging.getLogger(__name__)


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


# views.py - модифицируйте функцию process_payment
from .yookassa_api import YooKassaAPI

# Инициализируем YooKassaAPI
yookassa_api = YooKassaAPI()


@api_view(['POST'])
@transaction.atomic
def process_payment(request):
    """
    API-представление для обработки платежа и создания заказа
    """
    try:
        # Получаем данные из запроса
        data = request.data
        customer_name = data.get('customer_name')
        customer_email = data.get('customer_email')
        customer_phone = data.get('customer_phone')
        delivery_method = data.get('delivery_method', 'pochta_russia')
        delivery_comment = data.get('delivery_comment', '')

        # Получаем корзину из сессии
        cart = request.session.get('cart', {})

        if not cart:
            return JsonResponse({
                'status': 'error',
                'message': 'Корзина пуста'
            }, status=400)

        # Рассчитываем общую стоимость
        total_price = 0
        for product_id, item_data in cart.items():
            try:
                product = Product.objects.get(pk=product_id)
                quantity = item_data['quantity']
                total_price += float(product.price) * quantity
            except Product.DoesNotExist:
                logger.warning(f"Product with ID {product_id} not found")
                continue

        # Создаем заказ
        order = Order(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            total_price=total_price,
            delivery_method=delivery_method,
            delivery_comment=delivery_comment
        )

        # Добавляем информацию о доставке в зависимости от метода
        if delivery_method == 'cdek':
            # Получаем данные для CDEK
            cdek_city_code = data.get('cdek_city_code', '')
            cdek_city_name = data.get('cdek_city_name', '')
            cdek_point_code = data.get('cdek_point_code', '')
            cdek_point_address = data.get('cdek_point_address', '')
            cdek_point_name = data.get('cdek_point_name', '')

            # Сохраняем данные CDEK
            order.delivery_city = cdek_city_name
            order.cdek_city_code = cdek_city_code
            order.cdek_pickup_point_code = cdek_point_code
            order.delivery_address = f"{cdek_point_name} ({cdek_point_address})"

            # Получаем стоимость доставки CDEK
            shipping_cost = data.get('shipping_cost', 0)
            order.shipping_cost = shipping_cost
        else:  # pochta_russia
            delivery_address = data.get('delivery_address', '')
            delivery_index = data.get('delivery_index', '')
            order.delivery_address = delivery_address
            order.postal_code = delivery_index
            # Получаем стоимость доставки Почтой России
            shipping_cost = data.get('shipping_cost', 0)
            order.shipping_cost = shipping_cost

        # Обновляем общую стоимость с учетом доставки
        order.total_price += float(order.shipping_cost)

        # Сохраняем заказ
        order.save()

        # Добавляем товары в заказ
        insufficient_items = []
        for product_id, item_data in cart.items():
            try:
                product = Product.objects.get(pk=product_id)
                quantity = item_data['quantity']

                # Проверяем наличие товара на складе
                if product.stock < quantity:
                    insufficient_items.append({
                        'id': product.id,
                        'name': product.name,
                        'available': product.stock,
                        'requested': quantity
                    })
                    continue

                # Создаем элемент заказа
                OrderItem.objects.create(
                    order=order,
                    merch=product,
                    quantity=quantity,
                    price=product.price
                )

                # Уменьшаем количество товара на складе
                product.stock -= quantity
                product.save()
            except Product.DoesNotExist:
                logger.warning(f"Product with ID {product_id} not found")
                continue

        # Если есть товары с недостаточным количеством на складе
        if insufficient_items:
            # Удаляем созданный заказ
            order.delete()

            return JsonResponse({
                'status': 'error',
                'message': 'Недостаточно товаров на складе',
                'insufficient_items': insufficient_items
            }, status=400)

        # Создаем платеж через YooKassa
        payment_result = yookassa_api.create_payment(order)

        if payment_result['status'] == 'error':
            # Если произошла ошибка при создании платежа, удаляем заказ
            order.delete()

            return JsonResponse({
                'status': 'error',
                'message': f"Ошибка при создании платежа: {payment_result['message']}"
            }, status=500)

        # Сохраняем ID платежа и статус в заказе
        order.payment_id = payment_result['payment_id']
        order.payment_status = payment_result['payment_status']
        order.save()

        # Очищаем корзину
        request.session['cart'] = {}
        request.session.modified = True

        # Возвращаем успешный ответ с URL для оплаты
        return JsonResponse({
            'status': 'success',
            'message': 'Заказ успешно оформлен',
            'order_id': order.id,
            'payment_id': payment_result['payment_id'],
            'confirmation_url': payment_result['confirmation_url']
        })
    except Exception as e:
        logger.error(f"Error in process_payment: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при обработке заказа: {str(e)}'
        }, status=500)

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


@api_view(['GET'])
def calculate_cdek_shipping(request):
    """
    API-представление для расчета стоимости доставки CDEK
    """
    try:
        # Получаем параметры запроса
        city_code = request.GET.get('city_code', '')
        city_name = request.GET.get('city_name', '')
        address = request.GET.get('address', '')
        weight = request.GET.get('weight', 0)

        # Логирование для отладки
        logger.info(
            f"CDEK shipping calculation request: city_code={city_code}, city_name={city_name}, address={address}, weight={weight}")

        try:
            weight = int(weight)
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Вес должен быть числом'
            }, status=400)

        if not city_code:
            return JsonResponse({
                'status': 'error',
                'message': 'Необходимо указать код города'
            }, status=400)

        if not address:
            return JsonResponse({
                'status': 'error',
                'message': 'Необходимо указать адрес доставки'
            }, status=400)

        # Если название города не указано, используем значение по умолчанию
        if not city_name:
            city_name = "Город получателя"

        # Получаем код города отправления из настроек
        from_location_code = getattr(settings, 'CDEK_FROM_LOCATION_CODE', 44)

        # Инициализируем API CDEK
        cdek_api = CDEKApi(
            client_id=settings.CDEK_CLIENT_ID,
            client_secret=settings.CDEK_CLIENT_SECRET
        )

        # Используем tarifflist для расчета стоимости доставки
        tarifflist_result = cdek_api.calculate_tarifflist(
            from_location_code=from_location_code,
            to_location_code=city_code,
            to_city_name=city_name,
            to_address=address,
            weight=weight
        )

        if "error" in tarifflist_result:
            return JsonResponse({
                'status': 'error',
                'message': f"Ошибка расчета тарифа: {tarifflist_result['error']}"
            }, status=400)

        # Извлекаем стоимость доставки из ответа tarifflist
        shipping_cost = 300  # Значение по умолчанию
        delivery_time = None

        # Ищем тариф с кодом 136 (посылка склад-склад) или другой подходящий тариф
        if "tariff_codes" in tarifflist_result and tarifflist_result["tariff_codes"]:
            for tariff in tarifflist_result["tariff_codes"]:
                # Проверяем, есть ли тариф с кодом 136 (склад-склад)
                if tariff.get("tariff_code") == 136:
                    shipping_cost = tariff.get("delivery_sum", 300)
                    delivery_time = {
                        "min_days": tariff.get("period_min", 0),
                        "max_days": tariff.get("period_max", 0)
                    }
                    break

            # Если не нашли тариф 136, берем первый доступный тариф
            if shipping_cost == 300 and tarifflist_result["tariff_codes"]:
                first_tariff = tarifflist_result["tariff_codes"][0]
                shipping_cost = first_tariff.get("delivery_sum", 300)
                delivery_time = {
                    "min_days": first_tariff.get("period_min", 0),
                    "max_days": first_tariff.get("period_max", 0)
                }
        else:
            logger.warning(f"No tariff_codes found in CDEK API response: {tarifflist_result}")

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
        logger.error(f"Error in calculate_cdek_shipping: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Внутренняя ошибка сервера: {str(e)}'
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


@api_view(['GET'])
def suggest_cdek_cities(request):
    """
    API-представление для поиска городов CDEK по названию
    """
    try:
        # Получаем параметр запроса
        city_name = request.GET.get('query', '')

        if not city_name or len(city_name) < 3:
            return JsonResponse({
                'status': 'error',
                'message': 'Введите не менее 3 символов для поиска'
            }, status=400)

        # Инициализируем API CDEK с вашими учетными данными
        cdek_api = CDEKApi(
            client_id=settings.CDEK_CLIENT_ID,
            client_secret=settings.CDEK_CLIENT_SECRET
        )

        # Получаем результаты поиска
        result = cdek_api.suggest_cities(city_name)

        if 'error' in result:
            return JsonResponse({
                'status': 'error',
                'message': result['error']
            }, status=400)

        # Возвращаем результаты в формате, удобном для фронтенда
        return JsonResponse({
            'status': 'success',
            'cities': result['cities']
        })

    except Exception as e:
        logger.error(f"Error in suggest_cdek_cities: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }, status=500)


@api_view(['GET'])
def get_cdek_delivery_points(request):
    """
    API-представление для получения пунктов выдачи CDEK по коду города
    """
    try:
        # Получаем параметр запроса
        city_code = request.GET.get('city_code')
        if not city_code:
            return JsonResponse({
                'status': 'error',
                'message': 'Не указан код города'
            }, status=400)

        # Инициализируем API CDEK
        cdek_api = CDEKApi(
            client_id=settings.CDEK_CLIENT_ID,
            client_secret=settings.CDEK_CLIENT_SECRET
        )

        # Получаем пункты выдачи
        result = cdek_api.get_delivery_points(city_code)

        if "error" in result:
            return JsonResponse({
                'status': 'error',
                'message': result["error"]
            }, status=400)

        # Возвращаем результаты
        return JsonResponse(result)

    except Exception as e:
        logger.error(f"Error in get_cdek_delivery_points: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=500)




# Инициализируем YooKassaAPI
yookassa_api = YooKassaAPI()


# views.py - добавьте новое представление
@api_view(['POST'])
def check_payment_status(request):
    """
    Проверка статуса платежа
    """
    try:
        # Получаем ID заказа из запроса
        order_id = request.data.get('order_id')
        if not order_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Order ID is required'
            }, status=400)

        # Получаем заказ из базы данных
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Order not found'
            }, status=404)

        # Если у заказа нет ID платежа, возвращаем ошибку
        if not order.payment_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Payment ID not found for this order'
            }, status=400)

        # Проверяем статус платежа
        result = yookassa_api.check_payment_status(order.payment_id)

        if result['status'] == 'success':
            # Обновляем статус платежа в заказе
            order.payment_status = result['payment_status']
            if result['payment_status'] == 'succeeded':
                order.status = 'paid'
            order.save()

            return JsonResponse({
                'status': 'success',
                'payment_status': result['payment_status'],
                'order_status': order.status
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result['message']
            }, status=500)

    except Exception as e:
        logger.error(f"Error in check_payment_status: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Payment status check error: {str(e)}'
        }, status=500)


# views.py - добавьте представление для обработки уведомлений
@api_view(['POST'])
@csrf_exempt
def payment_webhook(request):
    """
    Обработчик уведомлений от YooKassa
    """
    try:
        # Получаем данные из запроса
        event_json = request.body.decode('utf-8')

        # Парсим JSON
        import json
        event_data = json.loads(event_json)

        # Получаем тип события и объект
        event_type = event_data.get('event')
        payment_data = event_data.get('object')

        if event_type == 'payment.succeeded':
            # Платеж успешно завершен
            payment_id = payment_data.get('id')
            metadata = payment_data.get('metadata', {})
            order_id = metadata.get('order_id')

            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    order.payment_status = 'succeeded'
                    order.status = 'paid'
                    order.save()
                    logger.info(f"Payment {payment_id} for order {order_id} succeeded")
                except Order.DoesNotExist:
                    logger.error(f"Order {order_id} not found for payment {payment_id}")

        elif event_type == 'payment.canceled':
            # Платеж отменен
            payment_id = payment_data.get('id')
            metadata = payment_data.get('metadata', {})
            order_id = metadata.get('order_id')

            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    order.payment_status = 'canceled'
                    order.save()
                    logger.info(f"Payment {payment_id} for order {order_id} canceled")
                except Order.DoesNotExist:
                    logger.error(f"Order {order_id} not found for payment {payment_id}")

        return JsonResponse({'status': 'success'})

    except Exception as e:
        logger.error(f"Error in payment_webhook: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)