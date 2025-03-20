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
  async function processPayment(customerData) {
  loading.value = true;
  paymentStatus.value = '';
  paymentMessage.value = '';
  insufficientItems.value = [];

  try {
    console.log('Отправка данных платежа на сервер:', customerData);

    // Отправляем данные в формате, который ожидает сервер
    const response = await axios.post('/api/process_payment/', customerData);

    // Обработка ответа
    paymentStatus.value = response.data.status;
    paymentMessage.value = response.data.message;

    if (response.data.insufficient_items) {
      insufficientItems.value = response.data.insufficient_items;
    }

    if (response.data.status === 'success') {
      // Очистка корзины после успешной оплаты
      cartProducts.value = [];
      totalQuantity.value = 0;
      totalPrice.value = 0;
      totalWeight.value = 0;
    }

    return response.data;
  } catch (err) {
    console.error('Ошибка при обработке платежа:', err);

    // Если сервер вернул ответ с ошибкой, выводим его
    if (err.response && err.response.data) {
      console.error('Ответ сервера с ошибкой:', err.response.data);
      paymentMessage.value = err.response.data.message || 'Произошла ошибка при обработке платежа';
    } else {
      paymentMessage.value = 'Произошла ошибка при обработке платежа';
    }

    error.value = err;
    paymentStatus.value = 'error';

    return {
      status: 'error',
      message: paymentMessage.value
    };
  } finally {
    loading.value = false;
  }
}
// asd

async function normalizeAddress(address) {
  try {
    const response = await fetch('/api/normalize-address/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ address })
    });

    const data = await response.json();
    console.log('Response:', data);
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}
function saveNormalizedAddress(apiResponse) {
  // Если ответ от API содержит массив, берем первый элемент
  const addressData = Array.isArray(apiResponse) ? apiResponse[0] : apiResponse;

  // Возвращаем объект с нужными полями
  return {
    index: addressData.index,
    region: addressData.region,
    place: addressData.place,
    location: addressData.location,
    street: addressData.street,
    house: addressData.house,
    building: addressData.building,
    corpus: addressData.corpus,
    room: addressData.room
  };
}

function formatAddress(normalizedAddress) {
  if (!normalizedAddress) return '';

  const parts = [];

  // Добавляем индекс
  if (normalizedAddress.index) parts.push(normalizedAddress.index);

  // Добавляем регион
  if (normalizedAddress.region) parts.push(normalizedAddress.region);

  // Добавляем город только если он отличается от региона
  if (normalizedAddress.place && normalizedAddress.place !== normalizedAddress.region) {
    parts.push(normalizedAddress.place);
  }

  // Добавляем микрорайон/район
  if (normalizedAddress.location) parts.push(normalizedAddress.location);

  // Добавляем улицу только если она есть
  if (normalizedAddress.street) parts.push(normalizedAddress.street);

  // Добавляем дом и остальные части адреса
  if (normalizedAddress.house) parts.push(normalizedAddress.house);

  // Добавляем корпус
  if (normalizedAddress.building) parts.push(`корп. ${normalizedAddress.building}`);

  // Добавляем строение
  if (normalizedAddress.corpus) parts.push(`стр. ${normalizedAddress.corpus}`);

  // Добавляем квартиру/офис
  if (normalizedAddress.room) parts.push(`кв. ${normalizedAddress.room}`);

  // Соединяем все части запятыми
  return parts.join(', ');
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
    saveNormalizedAddress,
    formatAddress
  };
});