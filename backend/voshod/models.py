from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=50)  # Размеры (S, M, L, XL)
    weight = models.DecimalField(max_digits=10, decimal_places=2)  # Вес в кг
    image = models.ImageField(upload_to='images', null=True)  # Изображение товара
    stock = models.PositiveIntegerField()  # Количество на складе

    def __str__(self):
        return self.name
class Order(models.Model):
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending')  # Статус заказа
    customer_address = models.TextField(blank=True, null=True, verbose_name="Адрес доставки")
    postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Почтовый индекс")
    def __str__(self):
        return f"Order #{self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    merch = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.merch.name} x {self.quantity}"
