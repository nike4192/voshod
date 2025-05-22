from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


# В utils.py
def send_order_confirmation_email(order):
    """
    Отправляет электронное письмо с подтверждением заказа
    """
    # Проверяем, было ли уже отправлено письмо
    if order.email_sent:
        return False  # Письмо уже отправлено

    subject = f'Подтверждение заказа #{order.id}'

    # Создаем контекст для шаблона письма
    context = {
        'order': order,
        'order_items': order.orderitem_set.all(),
        'total_price': order.total_price,
        'shipping_cost': order.shipping_cost,
    }

    # Рендерим HTML-содержимое письма из шаблона
    html_message = render_to_string('emails/order_confirmation.html', context)
    # Простой текстовый вариант письма
    plain_message = f'Спасибо за заказ #{order.id}! Сумма заказа: {order.total_price} руб.'

    # Отправляем письмо
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
        html_message=html_message,
        fail_silently=False,
    )

    # Отмечаем, что письмо отправлено
    order.email_sent = True
    order.save(update_fields=['email_sent'])

    return True


def send_shipping_notification(order, tracking_number=None):
    """
    Отправляет уведомление о начале доставки заказа
    """
    # Обновляем трек-номер, если он был предоставлен
    if tracking_number:
        order.tracking_number = tracking_number
        order.save(update_fields=['tracking_number'])

    subject = f'Ваш заказ #{order.id} отправлен!'

    # Создаем контекст для шаблона письма
    context = {
        'order': order,
        'order_items': order.orderitem_set.all(),
        'tracking_number': order.tracking_number,
        'has_tracking': bool(order.tracking_number),
        'delivery_method': order.get_delivery_method_display() if hasattr(order,
                                                                          'get_delivery_method_display') else order.delivery_method,
    }

    # Рендерим HTML-содержимое письма из шаблона
    html_message = render_to_string('emails/shipping_notification.html', context)

    # Простой текстовый вариант письма
    plain_message = f'Ваш заказ #{order.id} отправлен!'
    if order.tracking_number:
        plain_message += f' Трек-номер для отслеживания: {order.tracking_number}'

    # Отправляем письмо
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
        html_message=html_message,
        fail_silently=False,
    )

    # Обновляем статус отправки уведомления
    order.shipping_notification_sent = True
    order.save(update_fields=['shipping_notification_sent'])

    return True