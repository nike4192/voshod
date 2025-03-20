# merch/admin.py
from django.contrib import admin
from .models import Product
from .models import Order, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock')  # Поля, отображаемые в списке
    list_editable = ('price', 'stock')  # Поля, которые можно редактировать прямо в списке
    search_fields = ('name', 'description')  # Поля для поиска
    list_filter = ('price', 'stock')  # Фильтры


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Добавляем новые поля в список отображаемых полей
    list_display = ('id', 'customer_name', 'customer_email', 'postal_code', 'total_price', 'status', 'created_at')

    # Добавляем фильтры по статусу и дате создания
    list_filter = ('status', 'created_at')

    # Добавляем поля для поиска
    search_fields = ('customer_name', 'customer_email', 'customer_phone', 'postal_code', 'customer_address')

    # Группируем поля в разделы для удобства
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Информация о доставке', {
            'fields': ('customer_address', 'postal_code')
        }),
        ('Информация о заказе', {
            'fields': ('total_price', 'status', 'created_at')
        }),
    )

    # Делаем поле created_at только для чтения
    readonly_fields = ('created_at',)

    inlines = [OrderItemInline]