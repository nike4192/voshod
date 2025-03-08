import { ref } from 'vue';
import { defineStore } from 'pinia';
import axios from 'axios';

export interface Product {
  id: number;
  name: string;
  price: number;
  description?: string;
  quantity?: number;
  total_price?: number;
  image_url?: string;
}

export const useCart = defineStore('useCart', function useCart() {
  const cartProducts = ref<Product[]>([]);
  const totalPrice = ref(0);
  const loading = ref(false);
  const error = ref(null);
  const paymentStatus = ref('');
  const paymentMessage = ref('');
  const insufficientItems = ref([]);

  async function fetchCartProducts() {
    loading.value = true;
    try {
      const response = await axios.get('/api/get_cart_products/');
      cartProducts.value = response.data.cart_products;
      totalPrice.value = response.data.total_price;
    } catch (err) {
      console.error('Ошибка при загрузке товаров в корзине:', err);
      error.value = err;
    } finally {
      loading.value = false;
    }
  }

  async function addCart(productId) {
    cartProducts.value = (await $fetch<Product[]>('/api/cart/' + productId + '/', {baseURL: 'http://localhost', method: "POST"})).cart;
  }

  async function removeFromCart(productId) {
    loading.value = true;
    try {
      await axios.delete(`/api/cart/remove/${productId}/`);
      await fetchCartProducts();
    } catch (err) {
      console.error('Ошибка при удалении товара из корзины:', err);
      error.value = err;
    } finally {
      loading.value = false;
    }
  }

  // Новая функция для обработки оплаты
  async function processPayment(customerData = {}) {
    loading.value = true;
    paymentStatus.value = '';
    paymentMessage.value = '';
    insufficientItems.value = [];

    try {
      const response = await axios.post('/api/process_payment/', customerData);
      paymentStatus.value = 'success';
      paymentMessage.value = response.data.message;
      // Очищаем корзину после успешной оплаты
      cartProducts.value = [];
      totalPrice.value = 0;
      return true;
    } catch (err) {
      console.error('Ошибка при обработке оплаты:', err);
      error.value = err;
      paymentStatus.value = 'error';

      if (err.response && err.response.data) {
        paymentMessage.value = err.response.data.message;
        if (err.response.data.insufficient_items) {
          insufficientItems.value = err.response.data.insufficient_items;
        }
      } else {
        paymentMessage.value = 'Произошла ошибка при обработке оплаты';
      }
      return false;
    } finally {
      loading.value = false;
    }
  }

  return {
    cartProducts,
    totalPrice,
    loading,
    error,
    paymentStatus,
    paymentMessage,
    insufficientItems,
    fetchCartProducts,
    addCart,
    removeFromCart,
    processPayment,
  };
});