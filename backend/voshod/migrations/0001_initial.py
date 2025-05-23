# Generated by Django 5.1.5 on 2025-05-06 20:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=255)),
                ('customer_email', models.EmailField(max_length=254)),
                ('customer_phone', models.CharField(max_length=20)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='pending', max_length=50)),
                ('delivery_address', models.TextField(blank=True, null=True, verbose_name='Адрес доставки')),
                ('postal_code', models.CharField(blank=True, max_length=20, null=True, verbose_name='Почтовый индекс')),
                ('delivery_method', models.CharField(default='pochta_russia', max_length=50, verbose_name='Способ доставки')),
                ('delivery_comment', models.TextField(blank=True, null=True, verbose_name='Комментарий к доставке')),
                ('delivery_city', models.CharField(blank=True, max_length=255, null=True, verbose_name='Город доставки')),
                ('cdek_city_code', models.CharField(blank=True, max_length=50, null=True, verbose_name='Код города CDEK')),
                ('cdek_pickup_point_code', models.CharField(blank=True, max_length=50, null=True, verbose_name='Код пункта выдачи CDEK')),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Стоимость доставки')),
                # ('payment_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='ID платежа YooKassa')),
                # ('payment_status', models.CharField(blank=True, max_length=50, null=True, verbose_name='Статус платежа')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('size', models.CharField(max_length=50)),
                ('weight', models.DecimalField(decimal_places=2, max_digits=10)),
                ('image', models.ImageField(null=True, upload_to='images')),
                ('stock', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена за единицу')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='voshod.order')),
                ('merch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='voshod.product')),
            ],
        ),
    ]
