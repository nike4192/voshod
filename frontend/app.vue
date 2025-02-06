<template>
  <div>
    <h1>Товары</h1>
    <ul>
      <li v-for="product in products" :key="product.id">
        {{ product.name }} - {{ product.price }} руб.
      </li>
    </ul>
    <p v-if="error">Ошибка: {{ error.message }}</p>
  </div>
</template>

<script setup>
import { useProducts } from '~/composables/useProduct';
const { products, error, fetchProducts } = useProducts();
// Загружаем товары при монтировании компонента
// fetchProducts();
</script>