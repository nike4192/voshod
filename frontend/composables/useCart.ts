import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';

export const useCart = defineStore('cart', () => {
  const cartProducts = ref([]);
  const totalPrice = ref(0);
  const totalQuantity = ref(0);
  const totalWeight = ref(0); // Новая переменная для хранения общего веса
  const loading = ref(false);
  const error = ref(null);
  const paymentStatus = ref('');
  const paymentMessage = ref('');
  const insufficientItems = ref([]);

  // Получение базовой информации о корзине
  async function fetchCart() {
    loading.value = true;
    try {
      const response = await axios.get('/api/cart/');
      if (response.data && response.data.cart) {
        cartProducts.value = response.data.cart;
        totalQuantity.value = response.data.total_quantity || 0;  // Получаем значение с бэкенда
      } else {
        cartProducts.value = [];
        totalQuantity.value = 0;
      }
    } catch (err) {
      console.error('Ошибка при получении корзины:', err);
      error.value = err;
      cartProducts.value = [];
      totalQuantity.value = 0;
    } finally {
      loading.value = false;
    }
  }

    async function fetchCartWeight() {
    loading.value = true;
    try {
      const response = await axios.get('/api/cart/weight/');
      totalWeight.value = response.data.total_weight || 0;
    } catch (err) {
      console.error('Ошибка при получении веса корзины:', err);
      error.value = err;
      totalWeight.value = 0;
    } finally {
      loading.value = false;
    }
  }

  // Получение подробной информации о товарах в корзине
  async function fetchCartProducts() {
    loading.value = true;
    try {
      const response = await axios.get('/api/get_cart_products/');
      cartProducts.value = response.data.cart_products || [];
      totalPrice.value = response.data.total_price || 0;
      totalQuantity.value = response.data.total_quantity || 0;

      // Получаем вес корзины
      await fetchCartWeight();
    } catch (err) {
      console.error('Ошибка при получении товаров корзины:', err);
      error.value = err;
      cartProducts.value = [];
      totalPrice.value = 0;
      totalQuantity.value = 0;
      totalWeight.value = 0;
    } finally {
      loading.value = false;
    }
  }

  // Добавление товара в корзину
  async function addCart(productId) {
    loading.value = true;
    try {
      const response = await axios.post(`/api/cart/${productId}/`);
      console.log('Товар добавлен в корзину:', response.data);
      await fetchCartProducts(); // Обновляем корзину после добавления
      return true;
    } catch (err) {
      console.error('Ошибка при добавлении товара в корзину:', err);
      error.value = err;
      return false;
    } finally {
      loading.value = false;
    }
  }

  // Удаление товара из корзины
  async function removeFromCart(productId) {
    loading.value = true;
    try {
      await axios.delete(`/api/cart/remove/${productId}/`);
      console.log('Товар удален из корзины:', productId);
      await fetchCartProducts(); // Обновляем корзину после удаления
      return true;
    } catch (err) {
      console.error('Ошибка при удалении товара из корзины:', err);
      error.value = err;
      return false;
    } finally {
      loading.value = false;
    }
  }

  // Обработка оплаты
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
// asd

  async function normalizeAddress(address: string) {
  loading.value = true;
  try {
    const response = await axios.post('/api/normalize-address/', { address });
    return response.data;
  } catch (err) {
    console.error('Ошибка при нормализации адреса:', err);
    error.value = err;
    return {
      status: 'error',
      message: err.response?.data?.message || err.message
    };
  } finally {
    loading.value = false;
  }
}

  return {
    cartProducts,
    totalPrice,
    totalQuantity,
    totalWeight, // Добавляем в возвращаемый объект
    loading,
    error,
    paymentStatus,
    paymentMessage,
    insufficientItems,
    fetchCartProducts,
    fetchCartWeight, // Добавляем в возвращаемый объект
    fetchCart,
    addCart,
    removeFromCart,
    normalizeAddress,
    processPayment,
  };
});