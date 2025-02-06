# merch/admin.py
from django.contrib import admin
from .models import Product
from .models import Order, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock')  # Поля, отображаемые в списке
    list_editable = ('price', 'stock')        # Поля, которые можно редактировать прямо в списке
    search_fields = ('name', 'description')   # Поля для поиска
    list_filter = ('price', 'stock')          # Фильтры


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'total_price', 'status')
    inlines = [OrderItemInline]