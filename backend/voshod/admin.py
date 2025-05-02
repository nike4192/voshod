# merch/admin.py
from django.contrib import admin
from .models import Product, Order, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock')  # Поля, отображаемые в списке
    list_editable = ('price', 'stock')  # Поля, которые можно редактировать прямо в списке
    search_fields = ('name', 'description')  # Поля для поиска
    list_filter = ('price', 'stock')  # Фильтры


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    # Добавляем поле price в инлайн-форму
    fields = ('merch', 'quantity', 'price')
    readonly_fields = ('price',)  # Делаем поле price только для чтения в инлайн-форме


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Обновляем список отображаемых полей с учетом новых полей
    list_display = (
        'id',
        'customer_name',
        'customer_email',
        'delivery_method',
        'total_price',
        'shipping_cost',
        'status',
        'created_at'
    )

    # Обновляем фильтры
    list_filter = ('status', 'created_at', 'delivery_method')

    # Обновляем поля для поиска
    search_fields = (
        'customer_name',
        'customer_email',
        'customer_phone',
        'postal_code',
        'delivery_address',
        'delivery_city'
    )

    # Обновляем группировку полей в разделы
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Информация о доставке', {
            'fields': (
                'delivery_method',
                'delivery_address',
                'postal_code',
                'delivery_city',
                'delivery_comment',
                'shipping_cost'
            )
        }),
        ('Информация о CDEK', {
            'classes': ('collapse',),  # Этот раздел будет свернут по умолчанию
            'fields': (
                'cdek_city_code',
                'cdek_pickup_point_code'
            )
        }),
        ('Информация о заказе', {
            'fields': ('total_price', 'status', 'created_at')
        }),
    )

    # Делаем некоторые поля только для чтения
    readonly_fields = ('created_at', 'shipping_cost')

    # Включаем инлайн-форму для элементов заказа
    inlines = [OrderItemInline]

    # Добавляем действия для изменения статуса заказа
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

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