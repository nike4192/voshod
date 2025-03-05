import { Ref, ref } from 'vue';
import { useAsyncData } from '#app'; // Или 'nuxt/app' в зависимости от версии Nuxt
import { defineStore } from 'pinia'
export interface Product {
  id: number;
  name: string;
  price: number;
}

export const useCart = defineStore('useCart', function useCart() {
  const cartRef = ref(null);
  const error = null;

  async function addCart(productId) {
    cartRef.value = (await $fetch<Product[]>('/api/cart/' + productId + '/', {baseURL: 'http://localhost', method: "POST"})).cart;
  }

  async function fetchCart(productId) {
    cartRef.value = (await $fetch<Product[]>('/api/cart/', {baseURL: 'http://localhost'})).cart;
  }

  // console.log(cart, error,);

  return {
    cartRef,
    fetchCart,
    error,
    addCart,
  };
})
