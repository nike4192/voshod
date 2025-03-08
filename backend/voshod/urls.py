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
from voshod.view import get_cart, add_cart, get_cart_products, remove_from_cart, process_payment, get_cart_weight

from .view import get_csrf_token

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
    path('api/get-csrf-token/', get_csrf_token, name='get-csrf-token'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# asd