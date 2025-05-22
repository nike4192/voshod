# merch/admin.py
from django.contrib import admin
from .models import Product, Order, OrderItem
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from .utils import send_shipping_notification

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock')  # Поля, отображаемые в списке
    list_editable = ('price', 'stock')  # Поля, которые можно редактировать прямо в списке
    search_fields = ('name', 'description')  # Поля для поиска
    list_filter = ('price', 'stock')  # Фильтры


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'customer_name', 'delivery_method', 'total_price', 'status', 'created_at', 'payment_status', 'shipping_notification_sent')
    list_filter = ('status', 'payment_status', 'shipping_notification_sent', 'delivery_method')
    search_fields = ('id', 'customer_name', 'customer_email', 'customer_phone')

    # Делаем некоторые поля только для чтения
    readonly_fields = ('created_at', 'shipping_cost', 'payment_id', 'shipping_notification_sent')

    # Включаем инлайн-форму для элементов заказа
    inlines = [OrderItemInline]

    # Добавляем действия для изменения статуса заказа
    actions = [
        'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled',
        'mark_payment_as_succeeded', 'mark_payment_as_cancelled', 'send_shipping_notification_action',
        'update_statuses_based_on_payment'
    ]

    def get_fieldsets(self, request, obj=None):
        """Динамически определяет отображаемые поля в зависимости от способа доставки"""
        common_fieldsets = [
            ('Информация о клиенте', {
                'fields': ('customer_name', 'customer_email', 'customer_phone')
            }),
            ('Информация о заказе', {
                'fields': ('total_price', 'status', 'created_at')
            }),
            ('Информация о платеже', {
                'fields': ('payment_id', 'payment_status', 'email_sent'),
            }),
        ]
        
        if obj and obj.delivery_method == 'cdek':
            delivery_fieldset = ('Информация о доставке', {
                'fields': (
                    'delivery_method',
                    'delivery_address',
                    'delivery_city',
                    'delivery_comment',
                    'shipping_cost',
                    'tracking_number',
                    'shipping_notification_sent',
                    'cdek_city_code',
                    'cdek_pickup_point_code'
                )
            })
        else:  # pochta_russia или любой другой случай
            delivery_fieldset = ('Информация о доставке', {
                'fields': (
                    'delivery_method',
                    'delivery_address',
                    'postal_code',
                    'delivery_comment',
                    'shipping_cost',
                    'tracking_number',
                    'shipping_notification_sent'
                )
            })
            
        return [delivery_fieldset] + common_fieldsets

    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')

    mark_as_processing.short_description = "Отметить как 'В обработке'"

    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')

    mark_as_shipped.short_description = "Отметить как 'Отправлен'"

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')

    mark_as_delivered.short_description = "Отметить как 'Доставлен'"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')

    mark_as_cancelled.short_description = "Отметить как 'Отменен'"

    def mark_payment_as_succeeded(self, request, queryset):
        queryset.update(payment_status='succeeded')

    mark_payment_as_succeeded.short_description = "Отметить платеж как 'Успешный'"

    def mark_payment_as_cancelled(self, request, queryset):
        queryset.update(payment_status='cancelled')

    mark_payment_as_cancelled.short_description = "Отметить платеж как 'Отмененный'"

    # Добавляем новое действие для отправки уведомления о доставке
    def send_shipping_notification_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Выберите только один заказ для отправки уведомления", level='error')
            return

        order = queryset.first()
        url = reverse(
            'admin:voshod_order_send_shipping_notification',
            args=[order.pk],
        )
        return HttpResponseRedirect(url)

    send_shipping_notification_action.short_description = "Отправить уведомление о доставке"

    # Добавляем URL для отправки уведомления
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/send-shipping-notification/',
                self.admin_site.admin_view(self.send_shipping_notification_view),
                name='voshod_order_send_shipping_notification',
            ),
        ]
        return custom_urls + urls

    # Добавляем представление для отправки уведомления
    def send_shipping_notification_view(self, request, object_id):
        order = self.get_object(request, object_id)

        # Если это POST-запрос, отправляем уведомление
        if request.method == 'POST':
            tracking_number = request.POST.get('tracking_number', '')

            # Обновляем трек-номер и отправляем уведомление
            send_shipping_notification(order, tracking_number)
            
            # Меняем статус заказа на "shipped"
            order.status = 'shipped'
            order.save()

            self.message_user(request, f"Уведомление об отправке для заказа #{order.id} успешно отправлено. Статус заказа изменен на 'Отправлен'.")

            url = reverse(
                'admin:voshod_order_change',
                args=[object_id],
            )
            return HttpResponseRedirect(url)

        # Если GET-запрос, показываем форму для ввода трек-номера
        context = {
            'title': f'Отправить уведомление о доставке для заказа #{order.id}',
            'order': order,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return TemplateResponse(request, 'admin/send_shipping_notification.html', context)

    # Обрабатываем нажатие кнопки на странице редактирования заказа
    def response_change(self, request, obj):
        if "_send_shipping_notification" in request.POST:
            url = reverse(
                'admin:voshod_order_send_shipping_notification',
                args=[obj.pk],
            )
            return HttpResponseRedirect(url)
        return super().response_change(request, obj)

    # Автоматически меняем статус заказа в зависимости от статуса платежа
    def save_model(self, request, obj, form, change):
        # Если статус платежа "succeeded" или "paid", меняем статус заказа на "processing"
        if obj.payment_status in ['succeeded', 'paid']:
            obj.status = 'processing'
        # Иначе, если статус не "shipped" или "delivered", ставим "pending"
        elif obj.status not in ['shipped', 'delivered', 'cancelled']:
            obj.status = 'pending'
            
        super().save_model(request, obj, form, change)
        
    # Добавляем действие для обновления статусов существующих заказов на основе статуса платежа
    def update_statuses_based_on_payment(self, request, queryset):
        updated_processing = 0
        updated_pending = 0
        
        for order in queryset:
            if order.payment_status in ['succeeded', 'paid']:
                if order.status != 'processing' and order.status not in ['shipped', 'delivered', 'cancelled']:
                    order.status = 'processing'
                    order.save()
                    updated_processing += 1
            else:
                if order.status not in ['processing', 'shipped', 'delivered', 'cancelled']:
                    order.status = 'pending'
                    order.save()
                    updated_pending += 1
        
        if updated_processing > 0 or updated_pending > 0:
            message = f"Обновлено заказов: {updated_processing} на 'В обработке' и {updated_pending} на 'Ожидающие'"
            self.message_user(request, message)
        else:
            self.message_user(request, "Все заказы уже имеют корректные статусы.")
    
    update_statuses_based_on_payment.short_description = "Обновить статусы заказов на основе статуса платежа"