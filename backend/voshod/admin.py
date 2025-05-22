# merch/admin.py
from django.contrib import admin
from .models import Product, Order, OrderItem
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from .utils import send_shipping_notification
from django.utils.html import format_html

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_available')
    list_editable = ('price', 'stock')
    search_fields = ('name', 'description')
    list_filter = ('price', 'stock')
    
    def is_available(self, obj):
        return obj.stock > 0
    is_available.boolean = True
    is_available.short_description = 'В наличии'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)
    fields = ('product', 'quantity', 'price', 'total_price')
    
    def total_price(self, obj):
        return obj.price * obj.quantity
    total_price.short_description = 'Итого'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'customer_name', 
        'total_price', 
        'status', 
        'created_at', 
        'payment_status', 
        'shipping_notification_sent',
        'delivery_method'
    )
    list_filter = (
        'status', 
        'payment_status', 
        'shipping_notification_sent',
        'delivery_method',
        'created_at'
    )
    search_fields = (
        'id', 
        'customer_name', 
        'customer_email', 
        'customer_phone',
        'tracking_number'
    )
    date_hierarchy = 'created_at'
    readonly_fields = (
        'created_at', 
        'shipping_cost', 
        'payment_id', 
        'shipping_notification_sent',
        'total_price'
    )
    inlines = [OrderItemInline]
    
    actions = [
        'mark_as_processing', 
        'mark_as_shipped', 
        'mark_as_delivered', 
        'mark_as_cancelled',
        'mark_payment_as_succeeded', 
        'mark_payment_as_cancelled', 
        'send_shipping_notification_action'
    ]

    fieldsets = (
        ('Информация о клиенте', {
            'fields': (
                'customer_name', 
                'customer_email', 
                'customer_phone'
            ),
            'classes': ('wide',)
        }),
        ('Информация о доставке', {
            'fields': (
                'delivery_method',
                'delivery_address',
                'postal_code',
                'delivery_city',
                'delivery_comment',
                'shipping_cost',
                'tracking_number',
                'shipping_notification_sent'
            ),
            'classes': ('wide',)
        }),
        ('Информация о CDEK', {
            'classes': ('collapse',),
            'fields': (
                'cdek_city_code',
                'cdek_pickup_point_code'
            )
        }),
        ('Информация о заказе', {
            'fields': (
                'total_price', 
                'status', 
                'created_at'
            ),
            'classes': ('wide',)
        }),
        ('Информация о платеже', {
            'fields': (
                'payment_id', 
                'payment_status', 
                'email_sent'
            ),
            'classes': ('wide',)
        }),
    )

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if request.user.is_superuser:
            return list_display
        return [field for field in list_display if field != 'shipping_notification_sent']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('customer').prefetch_related('items')

    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'Обновлено {updated} заказов')
    mark_as_processing.short_description = "Отметить как 'В обработке'"

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'Обновлено {updated} заказов')
    mark_as_shipped.short_description = "Отметить как 'Отправлен'"

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'Обновлено {updated} заказов')
    mark_as_delivered.short_description = "Отметить как 'Доставлен'"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'Обновлено {updated} заказов')
    mark_as_cancelled.short_description = "Отметить как 'Отменен'"

    def mark_payment_as_succeeded(self, request, queryset):
        updated = queryset.update(payment_status='succeeded')
        self.message_user(request, f'Обновлено {updated} заказов')
    mark_payment_as_succeeded.short_description = "Отметить платеж как 'Успешный'"

    def mark_payment_as_cancelled(self, request, queryset):
        updated = queryset.update(payment_status='cancelled')
        self.message_user(request, f'Обновлено {updated} заказов')
    mark_payment_as_cancelled.short_description = "Отметить платеж как 'Отмененный'"

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

    def send_shipping_notification_view(self, request, object_id):
        order = self.get_object(request, object_id)

        if request.method == 'POST':
            tracking_number = request.POST.get('tracking_number', '')
            send_shipping_notification(order, tracking_number)
            self.message_user(request, f"Уведомление об отправке для заказа #{order.id} успешно отправлено.")
            url = reverse(
                'admin:voshod_order_change',
                args=[object_id],
            )
            return HttpResponseRedirect(url)

        context = {
            'title': f'Отправить уведомление о доставке для заказа #{order.id}',
            'order': order,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return TemplateResponse(request, 'admin/send_shipping_notification.html', context)

    def response_change(self, request, obj):
        if "_send_shipping_notification" in request.POST:
            url = reverse(
                'admin:voshod_order_send_shipping_notification',
                args=[obj.pk],
            )
            return HttpResponseRedirect(url)
        return super().response_change(request, obj)