from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Product
from rest_framework.decorators import api_view

from .serializers import ProductSerializer


@api_view(['POST'])
def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    cart_item = cart.get(str(product.pk), {'quantity': 0})
    cart_item['quantity'] += 1
    cart[str(product.pk)] = cart_item
    request.session['cart'] = cart
    return JsonResponse({'status': 'success', 'cart': cart})

@api_view(['GET'])
def get_cart(request):
    cart = request.session.get('cart', {})
    return JsonResponse({'cart': cart})

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
