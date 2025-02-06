# merch/serializers.py
from rest_framework import serializers
from .models import Product
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
