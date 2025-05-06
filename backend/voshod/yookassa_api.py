# yookassa_api.py
import uuid
import logging
import traceback
from yookassa import Configuration, Payment
from django.conf import settings

logger = logging.getLogger(__name__)


class YooKassaAPI:
    """
    Класс для работы с API YooKassa
    """

    def __init__(self):
        # Инициализация YooKassa с данными из настроек
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
        self.return_url = settings.YOOKASSA_RETURN_URL

    def format_phone(self, phone):
        """
        Форматирует номер телефона для YooKassa
        """
        # Удаляем все нецифровые символы
        digits_only = ''.join(filter(str.isdigit, phone))

        # Если номер начинается с 8, заменяем на 7
        if digits_only.startswith('8') and len(digits_only) == 11:
            digits_only = '7' + digits_only[1:]

        # Если номер не начинается с 7, добавляем 7 в начало
        if not digits_only.startswith('7') and len(digits_only) <= 10:
            digits_only = '7' + digits_only

        return digits_only

    def create_payment(self, order):
        """
        Создание платежа в YooKassa
        Args:
            order: Объект заказа из модели Order
        Returns:
            dict: Словарь с данными о созданном платеже или ошибке
        """
        try:
            # Формируем описание платежа
            description = f"Оплата заказа №{order.id}"
            # Создаем идентификатор идемпотентности
            idempotence_key = str(uuid.uuid4())

            # Получаем товары в заказе
            order_items = order.orderitem_set.all()

            # Формируем список позиций для чека
            receipt_items = []
            for item in order_items:
                receipt_items.append({
                    "description": item.merch.name[:128],  # Ограничение YooKassa - 128 символов
                    "quantity": str(item.quantity),
                    "amount": {
                        "value": str(item.price),
                        "currency": "RUB"
                    },
                    "vat_code": "1",  # НДС 20%
                    "payment_subject": "commodity",  # Товар
                    "payment_mode": "full_payment"  # Полная оплата
                })

            # Добавляем доставку в чек, если она платная
            if order.shipping_cost and float(order.shipping_cost) > 0:
                receipt_items.append({
                    "description": "Доставка",
                    "quantity": "1.0",
                    "amount": {
                        "value": str(order.shipping_cost),
                        "currency": "RUB"
                    },
                    "vat_code": "1",  # НДС 20%
                    "payment_subject": "service",  # Услуга
                    "payment_mode": "full_payment"  # Полная оплата
                })

            # Проверка суммы платежа
            total_items_sum = sum(float(item.price) * item.quantity for item in order_items)
            if order.shipping_cost:
                total_items_sum += float(order.shipping_cost)

            # Округляем до 2 знаков после запятой
            total_items_sum = round(total_items_sum, 2)
            order_total = round(float(order.total_price), 2)

            # Логирование для отладки
            logger.debug(f"Order ID: {order.id}")
            logger.debug(f"Customer email: {order.customer_email}")
            logger.debug(f"Customer phone: {order.customer_phone}")
            logger.debug(f"Total price: {order.total_price}")
            logger.debug(f"Shipping cost: {order.shipping_cost}")
            logger.debug(f"Total items sum: {total_items_sum}")
            logger.debug(f"Order total: {order_total}")

            # Если суммы не совпадают, корректируем
            if total_items_sum != order_total:
                logger.warning(f"Total items sum ({total_items_sum}) doesn't match order total ({order_total})")
                # Используем сумму товаров вместо общей суммы заказа
                payment_amount = str(total_items_sum)
            else:
                payment_amount = str(order.total_price)

            # Форматируем телефон
            formatted_phone = self.format_phone(order.customer_phone)

            # Формируем данные для платежа с чеком
            payment_data = {
                "amount": {
                    "value": payment_amount,
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": self.return_url
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "order_id": order.id
                },
                "receipt": {
                    "customer": {
                        "email": order.customer_email
                    },
                    "items": receipt_items
                }
            }

            # Добавляем телефон в чек, если он есть
            if formatted_phone:
                payment_data["receipt"]["customer"]["phone"] = formatted_phone

            # Логируем данные платежа для отладки
            logger.debug(f"Payment data: {payment_data}")

            # Создаем платеж
            payment = Payment.create(payment_data, idempotence_key)

            # Возвращаем успешный результат
            return {
                'status': 'success',
                'payment_id': payment.id,
                'confirmation_url': payment.confirmation.confirmation_url,
                'payment_status': payment.status
            }
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': f'Payment creation error: {str(e)}'
            }

    def check_payment_status(self, payment_id):
        """
        Проверка статуса платежа
        Args:
            payment_id: Идентификатор платежа в YooKassa
        Returns:
            dict: Словарь с данными о статусе платежа или ошибке
        """
        try:
            # Получаем информацию о платеже
            payment = Payment.find_one(payment_id)
            return {
                'status': 'success',
                'payment_status': payment.status,
                'payment_method': payment.payment_method.type if payment.payment_method else None,
                'amount': payment.amount.value,
                'currency': payment.amount.currency,
                'created_at': payment.created_at,
                'metadata': payment.metadata
            }
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': f'Payment status check error: {str(e)}'
            }