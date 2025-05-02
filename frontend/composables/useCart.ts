import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';

export const useCart = defineStore('cart', () => {
  const cartProducts = ref([]);
  const totalPrice = ref(0);
  const totalQuantity = ref(0);
  const totalWeight = ref(0);
  const loading = ref(false);
  const error = ref(null);
  const paymentStatus = ref('');
  const paymentMessage = ref('');
  const insufficientItems = ref([]);
  const shippingCost = ref(0);
  const shippingLoading = ref(false);
  const shippingError = ref(null);
  const deliveryIndex = ref('');
  const isCalculatingShipping = ref(false);
  const selectedDeliveryMethod = ref('pochta_russia');
  const selectedCdekCity = ref(null);
  const selectedCdekPickupPoint = ref(null);

  // Функция для установки способа доставки
  const setDeliveryMethod = (method) => {
    selectedDeliveryMethod.value = method;
    // Сбрасываем стоимость доставки при смене способа
    shippingCost.value = 0;
    shippingError.value = null;
  };

  const totalWithShipping = computed(() => {
    return totalPrice.value + shippingCost.value;
  });

  const saveDeliveryIndex = (index) => {
    deliveryIndex.value = index;
  };

  // Функция для расчета стоимости доставки CDEK
const calculateCdekShipping = async () => {
  shippingLoading.value = true;
  shippingError.value = null;

  try {
    // Проверяем, что у нас есть все необходимые данные
    if (!selectedCdekCity.value) {
      console.error('Отсутствует выбранный город CDEK:', selectedCdekCity.value);
      throw new Error('Не выбран город для доставки СДЭК');
    }

    if (!selectedCdekPickupPoint.value) {
      console.error('Отсутствует выбранный пункт выдачи CDEK:', selectedCdekPickupPoint.value);
      throw new Error('Не выбран пункт выдачи СДЭК');
    }

    // Получаем код города, название города и адрес пункта выдачи
    const cityCode = selectedCdekCity.value.code || '';
    const cityName = selectedCdekCity.value.fullName || '';
    const address = selectedCdekPickupPoint.value.address || '';

    // Проверяем наличие необходимых данных
    if (!cityCode) {
      throw new Error('Отсутствует код города СДЭК');
    }

    if (!address) {
      throw new Error('Отсутствует адрес пункта выдачи СДЭК');
    }

    console.log('Расчет доставки CDEK для:', {
      cityCode,
      cityName,
      address,
      weight: totalWeight.value
    });

    // Отправляем запрос на расчет стоимости
    const response = await axios.get('/api/calculate-cdek-shipping/', {
      params: {
        city_code: cityCode,
        city_name: cityName,
        address: address,
        weight: Math.max(1, totalWeight.value) // Убедимся, что вес не меньше 1 грамма
      }
    });

    console.log('API Response for CDEK shipping calculation:', response.data);

    if (response.data.status === 'success') {
      shippingCost.value = parseFloat(response.data.shipping_cost);
      console.log('Установлена стоимость доставки СДЭК:', shippingCost.value);
    } else {
      throw new Error(response.data.message || 'Не удалось рассчитать стоимость доставки СДЭК');
    }
  } catch (error) {
    console.error('Ошибка при расчете стоимости доставки CDEK:', error);
    shippingError.value = error.message || 'Произошла ошибка при расчете стоимости доставки';
    // Устанавливаем стоимость по умолчанию
    shippingCost.value = 300;
  } finally {
    shippingLoading.value = false;
  }
};  // Функция для расчета стоимости доставки

  const calculateShipping = async () => {
    console.log('Начало расчета стоимости доставки');
    console.log('Выбранный способ доставки:', selectedDeliveryMethod.value);
    console.log('Текущий вес корзины:', totalWeight.value);
    console.log('Текущий индекс доставки:', deliveryIndex.value);

    // Проверяем, не выполняется ли уже расчет
    if (isCalculatingShipping.value) {
      console.log('Расчет доставки уже выполняется, пропускаем повторный запрос');
      return;
    }

    // Проверяем наличие товаров в корзине
    if (cartProducts.value.length === 0) {
      console.warn('Корзина пуста, но пытаемся рассчитать доставку');
      shippingError.value = 'Невозможно рассчитать стоимость доставки для пустой корзины.';
      shippingCost.value = 300; // Значение по умолчанию
      return;
    }

    // Если вес равен 0, но товары есть, устанавливаем минимальный вес
    if (totalWeight.value <= 0 && cartProducts.value.length > 0) {
      console.warn('Вес корзины равен 0, но товары есть. Устанавливаем минимальный вес 100 грамм.');
      // Используем минимальный вес 100 грамм для расчета
      totalWeight.value = 100;
    }

    shippingLoading.value = true;
    shippingError.value = null;
    isCalculatingShipping.value = true;

    // Устанавливаем таймаут для предотвращения бесконечного ожидания
    const timeoutId = setTimeout(() => {
      if (shippingLoading.value) {
        shippingLoading.value = false;
        isCalculatingShipping.value = false;
        shippingError.value = 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.';
        shippingCost.value = 300; // Значение по умолчанию
        console.error('Timeout exceeded while calculating shipping cost');
      }
    }, 15000); // 15 секунд таймаут

    try {
      // Проверяем метод доставки
      if (selectedDeliveryMethod.value === 'cdek') {
        // ====== Обработка доставки CDEK ======
        console.log('Расчет доставки СДЭК');
        await calculateCdekShipping();
      } else {
        // ====== Обработка доставки Почтой России ======
        console.log('Расчет доставки Почтой России');

        // Для Почты России проверяем наличие индекса
        if (!deliveryIndex.value) {
          throw new Error('Индекс доставки не указан. Пожалуйста, укажите адрес доставки.');
        }

        // Проверяем формат индекса
        if (!/^\d{6}$/.test(deliveryIndex.value)) {
          throw new Error('Некорректный формат индекса. Индекс должен состоять из 6 цифр.');
        }

        // Логика для Почты России
        const url = '/api/calculate-shipping/';
        console.log(`Используем API: ${url} для расчета доставки`);

        const requestData = {
          index_to: deliveryIndex.value,
          mass: Math.max(1, totalWeight.value), // Минимальный вес 1 грамм
          height: 2,
          length: 5,
          width: 197,
          mail_category: 'ORDINARY',
          mail_type: 'POSTAL_PARCEL',
          fragile: true
        };

        console.log('Отправка запроса на расчет доставки Почтой России:', requestData);

        const response = await axios.post(url, requestData, {
          timeout: 10000 // Устанавливаем таймаут для axios в 10 секунд
        });

        console.log('Получен ответ от сервера Почты России:', JSON.stringify(response.data, null, 2));

        if (response.data.status === 'success') {
          if (response.data.shipping_cost !== undefined) {
            shippingCost.value = parseFloat(response.data.shipping_cost);
            console.log('Установлена стоимость доставки Почтой России:', shippingCost.value);

            // Сохраняем информацию о сроках доставки, если она есть
            if (response.data.delivery_time) {
              console.log('Получена информация о сроках доставки:', response.data.delivery_time);
            }
          } else {
            console.warn('Поле shipping_cost отсутствует в ответе Почты России');
            shippingCost.value = 300; // Значение по умолчанию
            shippingError.value = 'Информация о стоимости доставки отсутствует в ответе. Используется стоимость по умолчанию.';
          }
        } else {
          console.warn('Ответ API Почты России имеет статус, отличный от success:', response.data.status);
          shippingError.value = response.data.message || 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.';
          // Используем значение по умолчанию в случае ошибки
          shippingCost.value = 300; // Значение по умолчанию
        }
      }
    } catch (err) {
      // Обработка ошибок
      console.error('Ошибка при расчете стоимости доставки:', err);

      // Сохраняем сообщение об ошибке
      if (err instanceof Error) {
        shippingError.value = err.message;
      } else {
        shippingError.value = 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.';
      }

      // Устанавливаем стоимость по умолчанию
      shippingCost.value = 300;

      // Если ошибка связана с сетевым запросом, добавляем дополнительную информацию
      if (err.response) {
        console.error('Ответ сервера с ошибкой:', err.response.data);
        if (err.response.data && err.response.data.message) {
          shippingError.value = err.response.data.message;
        }
      }
    } finally {
      clearTimeout(timeoutId); // Очищаем таймаут
      shippingLoading.value = false;
      isCalculatingShipping.value = false;
      console.log('Итоговая стоимость доставки:', shippingCost.value);

      // Дополнительная проверка - если стоимость доставки все еще 0, устанавливаем значение по умолчанию
      if (shippingCost.value === 0) {
        console.warn('После всех проверок стоимость доставки все еще 0, устанавливаем по умолчанию');
        shippingCost.value = 300;
        if (!shippingError.value) {
          shippingError.value = 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.';
        }
      }
    }
  };

  // Функция для установки выбранного города CDEK
  const setSelectedCdekCity = (city) => {
    selectedCdekCity.value = city;
    console.log('Сохранен выбранный город CDEK:', city);
  };

  // Функция для установки выбранного пункта выдачи CDEK
  const setSelectedCdekPickupPoint = (point) => {
    selectedCdekPickupPoint.value = point;
    console.log('Сохранен выбранный пункт выдачи CDEK:', point);
  };
    // Получение базовой информации о корзине
  const fetchCart = async () => {
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
  };

  // Получение веса корзины
  const fetchCartWeight = async () => {
    try {
      console.log('Запрос веса корзины...');
      const response = await axios.get('/api/cart/weight/');
      if (response.data && response.data.status === 'success') {
        console.log('Получен вес корзины:', response.data.total_weight);
        totalWeight.value = response.data.total_weight;
        // Если вес равен 0, но у нас есть товары, устанавливаем минимальный вес
        if (totalWeight.value <= 0 && cartProducts.value.length > 0) {
          console.warn('Полученный вес равен 0, но товары есть. Устанавливаем минимальный вес 100 грамм.');
          totalWeight.value = 100;
        }
      } else {
        console.warn('Некорректный ответ при запросе веса корзины:', response.data);
        // Если есть товары, но вес не получен, устанавливаем минимальный вес
        if (cartProducts.value.length > 0) {
          totalWeight.value = 100;
        } else {
          totalWeight.value = 0;
        }
      }
    } catch (err) {
      console.error('Ошибка при получении веса корзины:', err);
      // Если есть товары, но вес не получен из-за ошибки, устанавливаем минимальный вес
      if (cartProducts.value.length > 0) {
        totalWeight.value = 100;
      } else {
        totalWeight.value = 0;
      }
    }
  };

  // Получение подробной информации о товарах в корзине
  const fetchCartProducts = async () => {
    loading.value = true;
    error.value = null;

    try {
      console.log('Fetching cart products...');
      const response = await axios.get('/api/get_cart_products/');
      console.log('Response received:', response.data);

      // Проверяем структуру ответа
      if (response.data && response.data.status === 'success') {
        // Проверяем, есть ли cart_products в ответе
        if (response.data.cart_products && Array.isArray(response.data.cart_products)) {
          cartProducts.value = response.data.cart_products.map(product => ({
            ...product,
            // Убедимся, что числовые значения действительно числа
            price: typeof product.price === 'number' ? product.price : parseFloat(product.price) || 0,
            quantity: typeof product.quantity === 'number' ? product.quantity : parseInt(product.quantity) || 0,
            total: typeof product.total === 'number' ? product.total :
                   (typeof product.item_total === 'number' ? product.item_total :
                    parseFloat(product.total || product.item_total) || 0)
          }));
          console.log('Processed cart products:', cartProducts.value);

          // Устанавливаем общую стоимость и количество из ответа или вычисляем их
          totalPrice.value = typeof response.data.total_price === 'number' ?
                             response.data.total_price :
                             parseFloat(response.data.total_price) || 0;
          totalQuantity.value = typeof response.data.total_quantity === 'number' ?
                               response.data.total_quantity :
                               parseInt(response.data.total_quantity) || 0;
        } else {
          console.warn('No cart_products array found in response');
          cartProducts.value = [];
          totalPrice.value = 0;
          totalQuantity.value = 0;
        }
      } else {
        console.warn('Invalid response format or status is not success');
        cartProducts.value = [];
        totalPrice.value = 0;
        totalQuantity.value = 0;
      }
    } catch (err) {
      console.error('Error fetching cart products:', err);
      error.value = err;
      cartProducts.value = [];
      totalPrice.value = 0;
      totalQuantity.value = 0;
    } finally {
      loading.value = false;
    }
  };

  // Добавление товара в корзину
  const addCart = async (productId) => {
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
  };

  // Удаление товара из корзины
  const removeFromCart = async (productId) => {
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
  };

  // Обработка оплаты
  const processPayment = async (customerData) => {
    loading.value = true;
    error.value = null;
    paymentStatus.value = '';
    paymentMessage.value = '';
    insufficientItems.value = [];

    try {
      // Если стоимость доставки еще не рассчитана, пробуем рассчитать
      if (shippingCost.value === 0 && deliveryIndex.value) {
        await calculateShipping();
      }

      const response = await axios.post('/api/process_payment/', {
        ...customerData,
        shipping_cost: shippingCost.value,
        delivery_index: deliveryIndex.value,
        total_with_shipping: totalWithShipping.value,
        delivery_method: selectedDeliveryMethod.value // Добавляем информацию о способе доставки
      });

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
        shippingCost.value = 0;
        deliveryIndex.value = '';
      }

      return response.data;
    } catch (err) {
      console.error('Ошибка при обработке платежа:', err);

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
  };

  // Функция для нормализации адреса
  const normalizeAddress = async (address) => {
    try {
      console.log('Отправка запроса на нормализацию адреса:', address);
      const response = await fetch('/api/normalize-address/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ address })
      });

      const data = await response.json();
      console.log('Ответ от API нормализации адреса:', data);

      // Сохраняем полный ответ для отладки
      if (typeof window !== 'undefined') {
        window.lastNormalizedAddressResponse = data;
      }

      // Если нормализация прошла успешно, пытаемся извлечь индекс
      if (data.status === 'success') {
        let index = null;
        let normalizedAddress = data.normalized_address;
        console.log('Структура нормализованного адреса:', JSON.stringify(normalizedAddress, null, 2));

        // Пытаемся найти индекс в различных местах ответа
        if (normalizedAddress) {
          if (normalizedAddress.index) {
            index = normalizedAddress.index;
            console.log('Индекс найден в поле index:', index);
          } else if (normalizedAddress.postal_code) {
            index = normalizedAddress.postal_code;
            console.log('Индекс найден в поле postal_code:', index);
          } else if (typeof normalizedAddress === 'string' && /\d{6}/.test(normalizedAddress)) {
            const match = normalizedAddress.match(/\b(\d{6})\b/);
            if (match) {
              index = match[1];
              console.log('Индекс извлечен из строки адреса:', index);
            }
          }
          // Проверяем вложенные объекты
          else if (normalizedAddress.data && normalizedAddress.data.index) {
            index = normalizedAddress.data.index;
            console.log('Индекс найден во вложенном объекте data.index:', index);
          }
        }

        // Если индекс найден, сохраняем его
        if (index) {
          saveDeliveryIndex(index);
          console.log('Сохранен индекс:', index);
        } else {
          console.warn('Не удалось найти индекс в ответе API нормализации');
        }
      }

      return data;
    } catch (error) {
      console.error('Ошибка при нормализации адреса:', error);
      throw error;
    }
  };

  // Функция для сохранения нормализованного адреса
  const saveNormalizedAddress = (apiResponse) => {
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
  };

  // Функция для форматирования адреса
  const formatAddress = (normalizedAddress) => {
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
  };

  // Возвращаем объект хранилища с методами и свойствами
  return {
    cartProducts,
    totalPrice,
    totalQuantity,
    totalWeight,
    loading,
    error,
    paymentStatus,
    paymentMessage,
    insufficientItems,
    fetchCartProducts,
    fetchCartWeight,
    fetchCart,
    addCart,
    removeFromCart,
    normalizeAddress,
    processPayment,
    saveNormalizedAddress,
    formatAddress,
    shippingCost,
    shippingLoading,
    shippingError,
    deliveryIndex,
    totalWithShipping,
    calculateShipping,
    saveDeliveryIndex,
    isCalculatingShipping,
    selectedDeliveryMethod,
    setDeliveryMethod,
    selectedCdekCity,
    setSelectedCdekCity,
    selectedCdekPickupPoint,
    setSelectedCdekPickupPoint
  };
});