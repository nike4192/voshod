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

    # Поля для адреса доставки
    delivery_address = models.TextField(blank=True, null=True, verbose_name="Адрес доставки")
    postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Почтовый индекс")

    # Добавляем поля для способа доставки
    delivery_method = models.CharField(max_length=50, default='pochta_russia', verbose_name="Способ доставки")
    delivery_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий к доставке")

    # Поля для CDEK
    delivery_city = models.CharField(max_length=255, blank=True, null=True, verbose_name="Город доставки")
    cdek_city_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Код города CDEK")
    cdek_pickup_point_code = models.CharField(max_length=50, blank=True, null=True,
                                              verbose_name="Код пункта выдачи CDEK")

    # Стоимость доставки
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Стоимость доставки")

    # Новые поля для YooKassa
    payment_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID платежа YooKassa")
    payment_status = models.CharField(max_length=50, blank=True, null=True, verbose_name="Статус платежа")

    email_sent = models.BooleanField(default=False, verbose_name="Письмо отправлено")

    tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Трек-номер отправления")
    shipping_notification_sent = models.BooleanField(default=False, verbose_name="Уведомление об отправке отправлено")

    # payment_method = models.CharField(max_length=50, blank=True, null=True, verbose_name="Метод оплаты")
    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    merch = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу")

    def __str__(self):
        return f"{self.merch.name} x {self.quantity}"
