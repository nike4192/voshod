"""
URL configuration for voshod project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .serializers import ProductViewSet
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings
from voshod.view import get_cart, add_cart, get_cart_products, remove_from_cart, process_payment, get_cart_weight, normalize_address, address_suggestions, calculate_shipping_cost, calculate_cdek_shipping, suggest_cdek_cities, get_cdek_delivery_points, check_payment_status, payment_webhook

router = DefaultRouter()
router.register(r'product', ProductViewSet)

urlpatterns = [
    path('api/cart/weight/', get_cart_weight, name='get_cart_weight'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/cart/', get_cart),
    path('api/cart/<product_id>/', add_cart),
    path('api/get_cart_products/', get_cart_products, name='get_cart_products'),
    path('api/cart/remove/<product_id>/', remove_from_cart, name='remove_from_cart'),
    path('api/process_payment/', process_payment, name='process_payment'),
    path('api/normalize-address/', normalize_address, name='normalize_address'),
    path('api/address-suggestions/', address_suggestions, name='address_suggestions'),
    path('api/calculate-shipping/', calculate_shipping_cost, name='calculate_shipping_cost'),
    path('api/calculate-cdek-shipping/', calculate_cdek_shipping, name='calculate_cdek_shipping'),
    path('api/suggest-cities/', suggest_cdek_cities, name='suggest_cdek_cities'),
    path('api/cdek-delivery-points/', get_cdek_delivery_points, name='get_cdek_delivery_points'),

    path('payment-webhook/', payment_webhook, name='payment_webhook'),
    path('api/check-payment-status/', check_payment_status, name='check_payment_status'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# asd