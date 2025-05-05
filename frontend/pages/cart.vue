<template>
  <!-- Шапка на всю ширину -->

  <div class="cart-page">
  <div class="header-full-width">
    <div class="header-container">
      <NuxtLink to="/" class="brand-link">
        <h1 class="brand-name">Voshod</h1>
      </NuxtLink>
      <div class="header-buttons">
        <Button @click="home" class="p-button-primary home-button" icon="pi pi-home" tooltip="На главную"
                tooltipOptions="{position: 'bottom'}"/>
      </div>
    </div>
  </div>
  <div class="content-container">
    <h1>{{ currentStep === 'cart' ? 'Товары в корзине' : 'Оформление заказа' }}</h1>
    <div class="cart-page-wrapper">
      <div style="max-width:1400px;" class="m-auto">
        <!-- Индикатор шагов -->
        <div class="steps-container mb-4">
          <div class="step"
               :class="{ 'active': currentStep === 'cart' }"
               @click="goToCart">
            <span class="step-number">1</span>
            <span class="step-text">Корзина</span>
          </div>
          <div class="step-connector"></div>
          <div class="step"
               :class="{ 'active': currentStep === 'delivery' }"
               @click="goToDelivery">
            <span class="step-number">2</span>
            <span class="step-text">Доставка</span>
          </div>
          <div class="step-connector"></div>
          <div class="step"
               :class="{ 'active': currentStep === 'confirmation' }"
               @click="goToConfirmation">
            <span class="step-number">3</span>
            <span class="step-text">Подтверждение</span>
          </div>
        </div>
        <!-- Сообщения об ошибках или успешной оплате -->
        <div v-if="cartStore.paymentStatus === 'success'" class="payment-success">
          <h3>{{ cartStore.paymentMessage }}</h3>
          <p>Спасибо за ваш заказ!</p>
          <Button @click="home" label="Вернуться на главную" class="mt-3"/>
        </div>
        <div v-else-if="cartStore.paymentStatus === 'error'" class="payment-error">
          <h3>{{ cartStore.paymentMessage }}</h3>
          <div v-if="cartStore.insufficientItems && cartStore.insufficientItems.length > 0" class="mt-3">
            <h4>Недостаточно товаров на складе:</h4>
            <ul>
              <li v-for="insufficientItem in cartStore.insufficientItems" :key="insufficientItem.id">
                {{ insufficientItem.name }} - запрошено: {{ insufficientItem.requested }}, доступно:
                {{ insufficientItem.available }}
              </li>
            </ul>
          </div>
          <Button @click="currentStep = 'cart'" label="Вернуться к корзине" class="mt-3"/>
        </div>
        <div v-else>
          <div v-if="cartStore.loading">
            <ProgressSpinner/>
            <p>Загрузка...</p>
          </div>
          <div v-else-if="cartStore.cartProducts.length === 0">
            <div class="empty-cart">
              <i class="pi pi-shopping-cart empty-cart-icon"></i>
              <h2>Корзина пуста</h2>
              <p>Добавьте товары в корзину, чтобы продолжить покупки</p>
              <Button @click="home" label="Перейти к товарам" class="mt-3"/>
            </div>
          </div>
          <div v-else>
            <!-- Шаг 1: Корзина -->
            <div v-if="currentStep === 'cart'" class="cart-step">
              <div class="flex flex-column lg:flex-row">
                <div class="cart-items lg:w-8 pr-0 lg:pr-3">
                  <div v-for="item in cartStore.cartProducts" :key="item.id"
                       class="flex flex-row flex-wrap cart-item border-round-lg w-full align-items-center mb-3">

                    <div class="cart-item-image mr-3">
                      <img
                          v-if="item.image_url"
                          :src="item.image_url"
                          :alt="item.name"
                          class="product-image"
                      />
                      <div v-else class="image-placeholder">Нет изображения</div>
                    </div>

                    <div class="cart-item-details flex-grow-1">
                      <h3 class="m-0 mb-2">{{ item.name }}</h3>
                      <p class="m-0 mb-1">Цена: {{ item.price }} ₽</p>
                      <p class="m-0">Количество: {{ item.quantity }}</p>
                    </div>
                    <Button
                        @click="removeItem(item.id)"
                        class="p-button-danger p-button-sm"
                        icon="pi pi-trash"
                        :disabled="cartStore.loading"
                    ></Button>
                  </div>
                </div>
                <div class="cart-summary lg:w-4 mt-3 lg:mt-0" style="color:black">
                  <div class="p-4 border-round-lg summary-box">
                    <h3>Итого:</h3>
                    <div class="summary-row">
                      <span>Товары ({{ cartStore.totalQuantity }} шт.):</span>
                      <span>{{ cartStore.totalPrice }} ₽</span>
                    </div>
                    <div class="summary-row total">
                      <span>К оплате:</span>
                      <span>{{ cartStore.totalPrice }} ₽</span>
                    </div>
                    <Button
                        @click="goToDelivery"
                        label="Далее"
                        class="w-full mt-3"
                        :disabled="cartStore.loading"
                    ></Button>
                  </div>
                </div>
              </div>
            </div>
            <!-- Шаг 2: Форма доставки -->
            <div v-if="currentStep === 'delivery'" class="delivery-step">
              <h2>Информация о доставке</h2>
              <div class="p-fluid">
                <form @submit.prevent="goToConfirmation">
                  <div class="p-grid">
                    <div class="delivery-method-selection mb-4">
                      <h3>Выберите способ доставки</h3>

                      <div class="delivery-options">
                        <div class="delivery-option">
                          <RadioButton
                              v-model="customerData.delivery_method"
                              inputId="pochta"
                              name="delivery_method"
                              value="pochta_russia"
                              @change="handleDeliveryMethodChange"
                          />
                          <label for="pochta" class="delivery-label">
                            <img src="@/assets/Pochta_Russia.png" alt="Почта России" class="delivery-logo"/>
                            <span>Почта России</span>
                          </label>
                        </div>

                        <div class="delivery-option">
                          <RadioButton
                              v-model="customerData.delivery_method"
                              inputId="cdek"
                              name="delivery_method"
                              value="cdek"
                              @change="handleDeliveryMethodChange"
                          />
                          <label for="cdek" class="delivery-label">
                            <img src="@/assets/CDEK.png" alt="СДЭК" class="delivery-logo"/>
                            <span>СДЭК</span>
                          </label>
                        </div>
                      </div>
                    </div>
                    <div class="p-col-12 p-md-6">
                      <div class="p-field">
                        <label for="customer_name">Ваше имя</label>
                        <InputText
                            id="customer_name"
                            v-model="customerData.customer_name"
                            class="w-full"
                            :class="{ 'p-invalid': v$.customer_name.$invalid && v$.customer_name.$dirty }"
                        />
                        <small v-if="v$.customer_name.$invalid && v$.customer_name.$dirty" class="p-error">
                          {{ v$.customer_name.$errors[0].$message }}
                        </small>
                      </div>
                    </div>
                    <div class="p-col-12 p-md-6">
                      <div class="p-field">
                        <label for="customer_email">Email</label>
                        <InputText
                            id="customer_email"
                            v-model="customerData.customer_email"
                            class="w-full"
                            :class="{ 'p-invalid': v$.customer_email.$invalid && v$.customer_email.$dirty }"
                        />
                        <small v-if="v$.customer_email.$invalid && v$.customer_email.$dirty" class="p-error">
                          {{ v$.customer_email.$errors[0].$message }}
                        </small>
                      </div>
                    </div>
                    <div class="p-col-12 p-md-6">
                      <div class="p-field">
                        <label for="customer_phone">Телефон</label>
                        <InputText
                            id="customer_phone"
                            v-model="customerData.customer_phone"
                            class="w-full"
                            :class="{ 'p-invalid': v$.customer_phone.$invalid && v$.customer_phone.$dirty }"
                        />
                        <small v-if="v$.customer_phone.$invalid && v$.customer_phone.$dirty" class="p-error">
                          {{ v$.customer_phone.$errors[0].$message }}
                        </small>
                      </div>
                    </div>
                    <div v-if="!isCdekDelivery" class="field mb-4 address-field">
                      <label for="delivery_address" class="block mb-2">Адрес доставки</label>
                      <AddressNormalizer
                          v-model="customerData.delivery_address"
                          @address-normalized="handleAddressNormalized"
                          :error="v$.delivery_address.$error"
                      />
                    </div>

                    <!-- Поля для CDEK -->

                    <div v-if="customerData.delivery_method === 'cdek'">
                      <div class="p-col-12 p-md-6 pole">
                        <div class="p-field">
                          <label for="delivery_city">Город</label>
                          <CdekCitySelector
                              v-model="customerData.delivery_city"
                              :error="v$.delivery_city.$error"
                              @city-selected="handleCdekCitySelected"
                          />
                          <small v-if="v$.delivery_city.$error" class="p-error">
                            {{ v$.delivery_city.$errors[0].$message }}
                          </small>
                        </div>
                      </div>
                      <div class="p-col-12 p-md-6 pole">
                        <div class="p-field">
                          <label for="delivery_pickup_point">Пункт выдачи</label>
                          <CdekPickupPointSelector
                              v-model="customerData.delivery_pickup_point"
                              :city-code="selectedCdekCityCode"
                              :error="v$.delivery_pickup_point.$error"
                              @pickup-point-selected="handleCdekPickupPointSelected"
                          />
                          <small v-if="v$.delivery_pickup_point.$error" class="p-error">
                            {{ v$.delivery_pickup_point.$errors[0].$message }}
                          </small>
                        </div>
                      </div>
                    </div>
                    <div class="p-col-12" style="margin-top: 20px">
                      <div class="p-field">
                        <label for="delivery_comment">Комментарий к доставке (необязательно)</label>
                        <Textarea
                            id="delivery_comment"
                            v-model="customerData.delivery_comment"
                            class="w-full"
                            rows="3"
                        />
                      </div>
                    </div>
                  </div>
                  <div class="flex justify-content-between mt-4">
                    <Button label="Назад к корзине" @click="goToCart" outlined/>
                    <Button
                        label="Продолжить"
                        @click="goToConfirmation"
                        class="p-button-primary"
                    />
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- Шаг 3: Подтверждение -->
      <div v-if="currentStep === 'confirmation'">
        <h2>Подтверждение заказа</h2>

        <!-- Сводка заказа -->
        <div class="order-summary p-4 mb-4 summary-box">
          <h3>Ваш заказ</h3>

          <!-- Список товаров -->
          <div v-for="product in cartStore.cartProducts" :key="product.id" class="mb-2 d-flex justify-content-between">
            <span>{{ product.name || 'Товар' }} x {{ product.quantity || 1 }}</span>&nbsp;
            <span>
    {{ calculateProductTotal(product) }} ₽
  </span>
          </div>

          <hr/>

          <div class="d-flex justify-content-between mb-2 align-items-center">
            <span>Стоимость доставки:</span>
            <div class="d-flex align-items-center">
              <span class="mr-2">{{ cartStore.shippingCost.toFixed(2) }} ₽</span>
              <ProgressSpinner v-if="cartStore.shippingLoading" style="width:20px;height:20px" class="ml-2"/>
            </div>
          </div>

          <!-- Сообщение об ошибке и кнопка пересчета -->
          <div v-if="cartStore.shippingError" class="shipping-error-container mb-3">
            <div class="shipping-error-message">
              <i class="pi pi-exclamation-triangle mr-2" style="color: #dc3545;"></i>
              <span>{{ cartStore.shippingError }}</span>
            </div>
            <Button
                label="Пересчитать"
                @click="recalculateShipping"
                class="p-button-sm p-button-outlined p-button-danger"
                :loading="cartStore.shippingLoading"
                :disabled="cartStore.shippingLoading"
            />
          </div>

          <hr/>

          <!-- Итоговая сумма с доставкой -->
          <div class="d-flex justify-content-between font-weight-bold">
            <span>Итого к оплате:</span>
            <span>{{ cartStore.totalWithShipping.toFixed(2) }} ₽</span>
          </div>
        </div>
        <!-- Данные покупателя -->
        <div class="customer-info p-4 mb-4 summary-box">
          <h3>Данные получателя</h3>
          <p><strong>Имя:</strong> {{ customerData.customer_name }}</p>
          <p><strong>Email:</strong> {{ customerData.customer_email }}</p>
          <p><strong>Телефон:</strong> {{ customerData.customer_phone }}</p>

          <!-- Способ доставки -->
          <p><strong>Способ доставки:</strong>
            <span v-if="customerData.delivery_method === 'pochta_russia'">Почта России</span>
            <span v-else-if="customerData.delivery_method === 'cdek'">СДЭК</span>
          </p>

          <!-- Информация о доставке в зависимости от метода -->
          <template v-if="customerData.delivery_method === 'pochta_russia'">
            <p><strong>Адрес доставки:</strong> {{ customerData.delivery_address }}</p>
          </template>

          <template v-else-if="customerData.delivery_method === 'cdek'">
            <p><strong>Город:</strong> {{ cdekCityDisplay }}</p>
            <p><strong>Пункт выдачи:</strong> {{ cdekPickupPointDisplay }}</p>
          </template>

          <p v-if="customerData.delivery_comment"><strong>Комментарий:</strong> {{ customerData.delivery_comment }}</p>
        </div>

        <!-- Кнопки управления -->
        <div class="d-flex justify-content-between mt-4">
          <Button label="Назад" @click="goToDelivery" class="p-button-secondary"/>
          <Button
              label="Оплатить"
              @click="processPayment"
              :loading="cartStore.loading"
              :disabled="cartStore.loading || cartStore.shippingLoading || cartStore.shippingError"
              class="p-button-success"
          />
        </div>
      </div>
    </div>
  </div>
  <!-- Футер -->
<div class="footer">
  <div class="footer-container">
    <div class="footer-links">
      <NuxtLink to="/" class="footer-link">Главная</NuxtLink>
      <NuxtLink to="/offer" class="footer-link">Публичная оферта</NuxtLink>
      <NuxtLink to="/contacts" class="footer-link">Контакты</NuxtLink>
    </div>
    <div class="footer-copyright">
      © 2023 Voshod. Все права защищены.
    </div>
  </div>
</div>
  </div>
</template>

<script setup>
import {ref, computed, onMounted, watch} from 'vue';
import {useCart} from '~/composables/useCart.js';
import {useVuelidate} from '@vuelidate/core';
import {required, email, helpers} from '@vuelidate/validators';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Button from 'primevue/button';
import ProgressSpinner from 'primevue/progressspinner';
import AddressNormalizer from '~/components/AddressNormalizer.vue';
import {useRouter} from 'vue-router';
import {useToast} from 'primevue/usetoast';
import CdekCitySelector from '~/components/CdekCitySelector.vue';
import CdekPickupPointSelector from '~/components/CdekPickupPointSelector.vue';

const toast = useToast();
const router = useRouter();
const cartStore = useCart();
const selectedCdekCityCode = ref('');
const selectedCdekPickupPointCode = ref('');

// Текущий шаг оформления заказа
const currentStep = ref('cart');

// Данные покупателя
const customerData = ref({
  customer_name: '',
  customer_email: '',
  customer_phone: '',
  delivery_address: '',
  delivery_city: '',      // Новое поле для города
  delivery_pickup_point: '',
  delivery_comment: '',
  delivery_method: 'pochta_russia'
});

const isCdekDelivery = computed(() => {
  return customerData.value.delivery_method === 'cdek';
});

// Правила валидации
const rules = computed(() => {
  const baseRules = {
    customer_name: {required: helpers.withMessage('Введите ваше имя', required)},
    customer_email: {
      required: helpers.withMessage('Введите email', required),
      email: helpers.withMessage('Введите корректный email', email)
    },
    customer_phone: {required: helpers.withMessage('Введите номер телефона', required)}
  };

  // Добавляем правила в зависимости от метода доставки
  if (customerData.value.delivery_method === 'cdek') {
    return {
      ...baseRules,
      delivery_city: {required: helpers.withMessage('', required)},
      delivery_pickup_point: {required: helpers.withMessage('', required)}
    };
  } else {
    return {
      ...baseRules,
      delivery_address: {required: helpers.withMessage('', required)}
    };
  }
});

const v$ = useVuelidate(rules, customerData);

function handleDeliveryMethodChange() {
  console.log('Изменен способ доставки на:', customerData.value.delivery_method);

  // Устанавливаем выбранный способ доставки в хранилище
  cartStore.setDeliveryMethod(customerData.value.delivery_method);

  // Сбрасываем стоимость доставки
  cartStore.shippingCost = 0;
  cartStore.shippingError = null;

  // Если у нас уже есть индекс и вес, пересчитываем стоимость доставки
  if (cartStore.deliveryIndex && cartStore.totalWeight > 0) {
    cartStore.calculateShipping();
  }
}

function handleCdekCitySelected(city) {
  if (city) {
    selectedCdekCityCode.value = city.code;
    console.log('Выбран город CDEK:', city);

    // Если вам нужно сохранить дополнительные данные о городе
    if (cartStore.setSelectedCdekCity) {
      cartStore.setSelectedCdekCity(city);
    }
  } else {
    selectedCdekCityCode.value = '';
  }

  // Сбрасываем выбранный пункт выдачи при смене города
  customerData.value.delivery_pickup_point = '';
  selectedCdekPickupPointCode.value = '';
}

// Обработчик выбора пункта выдачи CDEK
function handleCdekPickupPointSelected(point) {
  if (point) {
    selectedCdekPickupPointCode.value = point.code;
    console.log('Выбран пункт выдачи CDEK:', point);

    // Сохраняем выбранный пункт выдачи в хранилище
    if (cartStore.setSelectedCdekPickupPoint) {
      // Сохраняем полную информацию о пункте выдачи
      cartStore.setSelectedCdekPickupPoint({
        code: point.code,
        address: point.address,
        name: point.name || '',
        workTime: point.workTime || '',
        phone: point.phone || ''
      });
    }
  } else {
    selectedCdekPickupPointCode.value = '';
    // Очищаем значение в хранилище
    if (cartStore.setSelectedCdekPickupPoint) {
      cartStore.setSelectedCdekPickupPoint(null);
    }
  }
}

// Ссылка на компонент AddressNormalizer
const addressNormalizerRef = ref(null);

// Информация о нормализованном адресе
const normalizedAddressInfo = ref(null);

// Функция для перехода на главную страницу
const home = () => {
  router.push('/');
};

// Функция для перехода к шагу "Корзина"
const goToCart = () => {
  if (currentStep.value !== 'cart') {
    currentStep.value = 'cart';
  }
};

function calculateProductTotal(product) {
  if (product.total !== undefined && typeof product.total === 'number') {
    return product.total.toFixed(2);
  } else if (product.price !== undefined && product.quantity !== undefined) {
    return (product.price * product.quantity).toFixed(2);
  } else {
    return '0.00'; // Возвращаем строку по умолчанию, если данные некорректны
  }
}

// Функция для перехода к шагу "Доставка"
const goToDelivery = () => {
  if (cartStore.cartProducts.length > 0) {
    currentStep.value = 'delivery';
  } else {
    toast.add({
      severity: 'warn',
      summary: 'Корзина пуста',
      detail: 'Добавьте товары в корзину, чтобы продолжить',
      life: 3000
    });
  }
};

// Функция для валидации адреса
const validateAddress = async () => {
  if (!customerData.value.delivery_address) return;

  try {
    // Проверяем, что компонент AddressNormalizer доступен
    if (addressNormalizerRef.value) {
      // Вызываем API для нормализации адреса
      const result = await addressNormalizerRef.value.normalizeAddress();

      // Сохраняем результат нормализации
      normalizedAddressInfo.value = result;

      console.log('Результат нормализации адреса:', result);
    }
  } catch (error) {
    console.error('Ошибка при нормализации адреса:', error);
  }
};

const cdekCityDisplay = computed(() => {
  if (customerData.value.delivery_method === 'cdek') {
    // Если есть выбранный город в хранилище
    if (cartStore.selectedCdekCity && cartStore.selectedCdekCity.fullName) {
      return cartStore.selectedCdekCity.fullName;
    }
    // Иначе используем значение из формы
    return customerData.value.delivery_city || 'Не указан';
  }
  return '';
});

const cdekPickupPointDisplay = computed(() => {
  if (customerData.value.delivery_method === 'cdek') {
    // Если есть выбранный пункт выдачи в хранилище
    if (cartStore.selectedCdekPickupPoint) {
      const address = cartStore.selectedCdekPickupPoint.address || '';

      // Получаем название города из выбранного города СДЭК
      let cityName = '';
      if (cartStore.selectedCdekCity && cartStore.selectedCdekCity.fullName) {
        // Извлекаем название города из полного названия (например, "Оренбург, Оренбургская область")
        const cityParts = cartStore.selectedCdekCity.fullName.split(',');
        cityName = cityParts[0].trim();
      }

      // Если не удалось получить название города из выбранного города, пытаемся извлечь из адреса
      if (!cityName) {
        const addressParts = address.split(',').map(part => part.trim());
        // Ищем часть адреса, которая содержит название города
        for (let i = 0; i < addressParts.length; i++) {
          const part = addressParts[i];
          // Обычно город идет после области/региона и перед улицей
          if (i >= 3 && !part.toLowerCase().includes('область') &&
              !part.toLowerCase().includes('ул.') && !part.toLowerCase().includes('улица')) {
            cityName = part;
            break;
          }
        }
      }

      // Ищем улицу (часть с "ул." или "улица")
      let street = '';
      const addressParts = address.split(',').map(part => part.trim());
      for (const part of addressParts) {
        if (part.toLowerCase().includes('ул.') || part.toLowerCase().includes('улица')) {
          street = part;
          break;
        }
      }

      // Если нашли и город, и улицу, формируем красивый адрес
      if (cityName && street) {
        return `${cityName}, ${street} (${address})`;
      }

      // Если не удалось найти город или улицу, возвращаем полный адрес
      return address;
    }

    // Если нет данных в хранилище, используем значение из формы
    return customerData.value.delivery_pickup_point || 'Не указан';
  }

  return '';
});

// Функция для перехода к шагу "Подтверждение"
async function goToConfirmation() {
  try {
    // Запускаем валидацию
    const isValid = await v$.value.$validate();

    if (!isValid) {
      toast.add({
        severity: 'error',
        summary: 'Ошибка',
        detail: 'Пожалуйста, заполните все обязательные поля корректно',
        life: 3000
      });
      return;
    }

    // Убедимся, что у нас есть вес корзины
    await ensureCartWeight();

    // Устанавливаем выбранный способ доставки в хранилище
    cartStore.setDeliveryMethod(customerData.value.delivery_method);

    // Обработка в зависимости от выбранного способа доставки
    if (customerData.value.delivery_method === 'cdek') {
      // ====== Обработка доставки CDEK ======

      // Проверяем, что данные выбраны и переданы в хранилище
      if (!cartStore.selectedCdekCity || !cartStore.selectedCdekPickupPoint) {
        console.log('Проверка данных CDEK:', {
          city: cartStore.selectedCdekCity,
          point: cartStore.selectedCdekPickupPoint
        });

        // Если данных нет в хранилище, но они есть в компоненте, передаем их
        if (selectedCdekCityCode.value && !cartStore.selectedCdekCity && cartStore.setSelectedCdekCity) {
          // Получаем данные города из компонента CdekCitySelector
          const cityElement = document.querySelector('.p-autocomplete-token-label');
          if (cityElement) {
            const cityName = cityElement.textContent;
            cartStore.setSelectedCdekCity({
              code: selectedCdekCityCode.value,
              fullName: cityName || 'Неизвестный город'
            });
          }
        }

        if (selectedCdekPickupPointCode.value && !cartStore.selectedCdekPickupPoint && cartStore.setSelectedCdekPickupPoint) {
          // Получаем данные пункта выдачи из компонента CdekPickupPointSelector
          const pointElement = document.querySelector('.p-dropdown-label');
          if (pointElement) {
            const pointAddress = pointElement.textContent;
            cartStore.setSelectedCdekPickupPoint({
              code: selectedCdekPickupPointCode.value,
              address: pointAddress || 'Неизвестный адрес'
            });
          }
        }
      }

      // Запускаем расчет доставки CDEK
      try {
        await cartStore.calculateShipping();
      } catch (error) {
        console.error('Ошибка при расчете доставки CDEK:', error);
        cartStore.shippingCost = 300;
        cartStore.shippingError = 'Не удалось рассчитать стоимость доставки CDEK. Используется стоимость по умолчанию.';
      }
    } else {
      // ====== Обработка доставки Почтой России ======

      // Если индекс доставки есть, но стоимость доставки еще не рассчитана, рассчитываем
      if (cartStore.deliveryIndex && cartStore.shippingCost === 0 && !cartStore.shippingLoading) {
        console.log('Расчет доставки Почтой России по имеющемуся индексу:', cartStore.deliveryIndex);
        try {
          await cartStore.calculateShipping();
        } catch (error) {
          console.error('Ошибка при расчете доставки Почтой России:', error);
          // Устанавливаем стоимость по умолчанию
          cartStore.shippingCost = 300;
          cartStore.shippingError = 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.';
        }
      }
      // Если индекса нет, но адрес есть, пытаемся извлечь индекс из адреса
      else if (!cartStore.deliveryIndex && customerData.value.delivery_address) {
        console.log('Попытка извлечь индекс из адреса:', customerData.value.delivery_address);
        const addressStr = customerData.value.delivery_address;
        const match = addressStr.match(/\b(\d{6})\b/);

        if (match) {
          console.log('Индекс извлечен из адреса:', match[1]);
          cartStore.saveDeliveryIndex(match[1]);

          try {
            await cartStore.calculateShipping();
          } catch (error) {
            console.error('Ошибка при расчете доставки после извлечения индекса:', error);
            // Устанавливаем стоимость по умолчанию
            cartStore.shippingCost = 300;
            cartStore.shippingError = 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.';
          }
        } else {
          console.warn('Индекс не найден в адресе, запрашиваем у пользователя');
          // Если индекс не найден, предлагаем пользователю ввести его вручную
          const userIndex = prompt('Пожалуйста, введите почтовый индекс для расчета стоимости доставки:', '');

          if (userIndex && /^\d{6}$/.test(userIndex.trim())) {
            console.log('Пользователь ввел индекс:', userIndex.trim());
            cartStore.saveDeliveryIndex(userIndex.trim());

            try {
              await cartStore.calculateShipping();
            } catch (error) {
              console.error('Ошибка при расчете доставки после ввода индекса пользователем:', error);
              cartStore.shippingCost = 300;
              cartStore.shippingError = 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.';
            }
          } else {
            console.warn('Пользователь не ввел корректный индекс');
            // Если индекс не найден, устанавливаем стоимость по умолчанию
            cartStore.shippingCost = 300;
            cartStore.shippingError = 'Не удалось определить индекс для расчета доставки. Используется стоимость по умолчанию.';
          }
        }
      }
      // Если ни индекса, ни адреса нет
      else if (!cartStore.deliveryIndex && !customerData.value.delivery_address) {
        console.warn('Ни индекс, ни адрес не указаны');
        cartStore.shippingCost = 300;
        cartStore.shippingError = 'Адрес доставки не указан. Используется стоимость по умолчанию.';
      }
      // Если стоимость доставки уже рассчитана
      else if (cartStore.shippingCost > 0) {
        console.log('Стоимость доставки уже рассчитана:', cartStore.shippingCost);
      }
      // Если что-то пошло не так
      else {
        console.warn('Неизвестная ситуация при расчете доставки');
        cartStore.shippingCost = 300;
        cartStore.shippingError = 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.';
      }
    }

    // Дополнительная проверка - если стоимость доставки все еще 0, устанавливаем значение по умолчанию
    if (cartStore.shippingCost === 0) {
      console.warn('После всех проверок стоимость доставки все еще 0, устанавливаем по умолчанию');
      cartStore.shippingCost = 300;
      if (!cartStore.shippingError) {
        cartStore.shippingError = 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.';
      }
    }

    // Переходим к шагу подтверждения
    currentStep.value = 'confirmation';

    // Прокручиваем страницу вверх для лучшего пользовательского опыта
    window.scrollTo({top: 0, behavior: 'smooth'});

  } catch (error) {
    console.error('Ошибка при переходе к подтверждению:', error);
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Произошла ошибка при обработке данных',
      life: 3000
    });
  }
}// Возврат к шагу доставки


// Вычисляемое свойство для форматированного адреса доставки
const formattedDeliveryAddress = computed(() => {
  if (normalizedAddressInfo.value && normalizedAddressInfo.value.normalized_address) {
    // Используем функцию из хранилища для форматирования адреса
    return cartStore.formatAddress(normalizedAddressInfo.value.normalized_address);
  }
  return customerData.value.delivery_address || 'Адрес не указан';
});

// Функция для удаления товара из корзины
const removeItem = async (productId) => {
  try {
    await cartStore.removeFromCart(productId);
    toast.add({
      severity: 'success',
      summary: 'Успех',
      detail: 'Товар удален из корзины',
      life: 3000
    });
  } catch (error) {
    console.error('Ошибка при удалении товара:', error);
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Не удалось удалить товар из корзины',
      life: 3000
    });
  }
};

// Функция для подтверждения заказа
async function processPayment() {
  if (cartStore.shippingLoading) {
    toast.add({
      severity: 'info',
      summary: 'Подождите',
      detail: 'Идет расчет стоимости доставки',
      life: 3000
    });
    return;
  }

  try {
    // Подготавливаем данные для отправки
    const orderData = {
      customer_name: customerData.value.customer_name,
      customer_email: customerData.value.customer_email,
      customer_phone: customerData.value.customer_phone,
      delivery_comment: customerData.value.delivery_comment || '',
      shipping_cost: cartStore.shippingCost,
      delivery_method: customerData.value.delivery_method
    };

    // Добавляем специфические данные в зависимости от метода доставки
    if (customerData.value.delivery_method === 'pochta_russia') {
      orderData.delivery_address = customerData.value.delivery_address;
      orderData.delivery_index = cartStore.deliveryIndex;
    } else if (customerData.value.delivery_method === 'cdek') {
      // Для СДЭК добавляем информацию о городе и пункте выдачи
      if (cartStore.selectedCdekCity) {
        orderData.cdek_city_code = cartStore.selectedCdekCity.code;
        orderData.cdek_city_name = cartStore.selectedCdekCity.fullName;
      }

      if (cartStore.selectedCdekPickupPoint) {
        orderData.cdek_point_code = cartStore.selectedCdekPickupPoint.code;
        orderData.cdek_point_address = cartStore.selectedCdekPickupPoint.address;
        orderData.cdek_point_name = cartStore.selectedCdekPickupPoint.name;
      }
    }

    console.log('Отправляемые данные заказа:', orderData);

    // Отправляем данные заказа на сервер
    const result = await cartStore.processPayment(orderData);

    if (result && result.status === 'success') {
      // Показываем сообщение об успешном оформлении заказа
      toast.add({
        severity: 'success',
        summary: 'Успех',
        detail: 'Заказ успешно оформлен!',
        life: 3000
      });

      // Переходим на главную страницу или страницу успешного оформления заказа
      setTimeout(() => {
        router.push('/');
      }, 2000);
    } else if (result && result.status === 'error') {
      // Показываем сообщение об ошибке
      toast.add({
        severity: 'error',
        summary: 'Ошибка',
        detail: result.message || 'Произошла ошибка при оформлении заказа',
        life: 5000
      });
    }
  } catch (error) {
    console.error('Ошибка при оформлении заказа:', error);
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Произошла ошибка при оформлении заказа',
      life: 5000
    });
  }
}


// Обработчик нормализации адреса
async function handleAddressNormalized(normalizedAddress) {
  console.log('Получен нормализованный адрес:', normalizedAddress);

  // Сохраняем нормализованный адрес в форме
  if (typeof normalizedAddress === 'string') {
    customerData.value.delivery_address = normalizedAddress;
    console.log('Сохранен строковый адрес:', normalizedAddress);
  } else if (normalizedAddress && normalizedAddress.address) {
    customerData.value.delivery_address = normalizedAddress.address;
    console.log('Сохранен адрес из поля address:', normalizedAddress.address);
  } else if (normalizedAddress) {
    // Используем существующую функцию форматирования
    customerData.value.delivery_address = cartStore.formatAddress(normalizedAddress);
    console.log('Сохранен отформатированный адрес:', customerData.value.delivery_address);
  }

  // Извлекаем индекс из нормализованного адреса
  let index = null;

  // Проверяем все возможные места, где может быть индекс
  if (normalizedAddress) {
    console.log('Структура нормализованного адреса:', JSON.stringify(normalizedAddress, null, 2));

    // Проверяем прямое поле index
    if (normalizedAddress.index) {
      index = normalizedAddress.index;
      console.log('Индекс найден в поле index:', index);
    }
    // Проверяем вложенные объекты
    else if (normalizedAddress.normalized_address && normalizedAddress.normalized_address.index) {
      index = normalizedAddress.normalized_address.index;
      console.log('Индекс найден во вложенном объекте normalized_address.index:', index);
    }
    // Другие проверки...
  }

  console.log('Итоговый извлеченный индекс:', index);

  if (!index) {
    console.warn('Не удалось извлечь индекс из нормализованного адреса');

    // Предлагаем пользователю ввести индекс вручную
    toast.add({
      severity: 'warn',
      summary: 'Внимание',
      detail: 'Не удалось определить почтовый индекс. Пожалуйста, введите его вручную для расчета стоимости доставки.',
      life: 5000
    });

    const userIndex = prompt('Пожалуйста, введите почтовый индекс для расчета стоимости доставки:', '');
    if (userIndex && /^\d{6}$/.test(userIndex.trim())) {
      index = userIndex.trim();
      console.log('Пользователь ввел индекс:', index);
    } else {
      console.warn('Пользователь не ввел корректный индекс');
      // Устанавливаем стоимость доставки по умолчанию
      cartStore.shippingCost = 300;
      cartStore.shippingError = 'Не удалось определить индекс для расчета доставки. Используется стоимость по умолчанию.';
      return;
    }
  }

  // Сохраняем индекс в хранилище
  cartStore.saveDeliveryIndex(index);

  // Убедимся, что у нас есть вес корзины
  await cartStore.fetchCartWeight();

  // Запускаем расчет доставки
  await cartStore.calculateShipping();
}

// Функция для пересчета стоимости доставки
async function recalculateShipping() {
  try {
    // Очищаем предыдущую ошибку
    cartStore.shippingError = null;

    // Проверяем наличие индекса
    if (!cartStore.deliveryIndex) {
      // Пытаемся извлечь индекс из адреса
      const addressStr = customerData.value.delivery_address;
      const match = addressStr.match(/\b(\d{6})\b/);
      if (match) {
        cartStore.saveDeliveryIndex(match[1]);
      } else {
        // Если индекс не найден, предлагаем пользователю ввести его вручную
        const indexInput = prompt('Пожалуйста, введите почтовый индекс для расчета доставки:', '');
        if (indexInput && /^\d{6}$/.test(indexInput.trim())) {
          cartStore.saveDeliveryIndex(indexInput.trim());
        } else {
          toast.add({
            severity: 'error',
            summary: 'Ошибка',
            detail: 'Пожалуйста, введите корректный 6-значный почтовый индекс',
            life: 3000
          });
          return;
        }
      }
    }

    // Убедимся, что у нас есть вес корзины
    await cartStore.fetchCartWeight();

    // Запускаем расчет доставки
    await cartStore.calculateShipping();

    // Если после расчета все еще есть ошибка, показываем уведомление
    if (cartStore.shippingError) {
      toast.add({
        severity: 'warn',
        summary: 'Предупреждение',
        detail: 'Не удалось рассчитать стоимость доставки. Используется стоимость по умолчанию.',
        life: 5000
      });
    } else {
      toast.add({
        severity: 'success',
        summary: 'Успех',
        detail: 'Стоимость доставки успешно рассчитана',
        life: 3000
      });
    }
  } catch (error) {
    console.error('Ошибка при пересчете стоимости доставки:', error);
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Произошла ошибка при пересчете стоимости доставки',
      life: 3000
    });

    // Устанавливаем стоимость по умолчанию при ошибке
    cartStore.shippingCost = 300;
    cartStore.shippingError = 'Произошла ошибка при расчете стоимости доставки. Используется стоимость по умолчанию.';
  }
}

// Функция для проверки и обновления веса корзины
async function ensureCartWeight() {
  console.log('Проверка веса корзины...');

  // Если вес равен 0 или не определен, запрашиваем его
  if (!cartStore.totalWeight || cartStore.totalWeight <= 0) {
    console.log('Вес корзины не определен или равен 0, запрашиваем...');
    await cartStore.fetchCartWeight();

    // Проверяем результат
    if (!cartStore.totalWeight || cartStore.totalWeight <= 0) {
      console.warn('Вес корзины все еще равен 0, устанавливаем минимальное значение');
      // Если вес все еще 0, но товары есть, устанавливаем минимальный вес
      if (cartStore.cartProducts.length > 0) {
        cartStore.totalWeight = 100; // Минимальный вес 100 грамм
      }
    }
  }

  console.log('Текущий вес корзины:', cartStore.totalWeight);
  return cartStore.totalWeight;
}

const hasItems = computed(() => {
  return cartStore.cartProducts.length > 0;
});

// Вычисляемое свойство для проверки возможности перехода к оформлению
const canProceedToCheckout = computed(() => {
  return hasItems.value && !cartStore.loading;
});

watch(() => cartStore.cartProducts, (newValue) => {
  if (newValue.length === 0 && currentStep.value !== 'cart') {
    // Если корзина опустела, возвращаемся к шагу корзины
    currentStep.value = 'cart';
    toast.add({
      severity: 'info',
      summary: 'Информация',
      detail: 'Корзина пуста',
      life: 3000
    });
  }
}, {deep: true});

// Отслеживаем изменения метода доставки для сброса валидации
watch(() => customerData.value.delivery_method, () => {
  // Сбрасываем ошибки валидации при изменении метода доставки
  v$.value.$reset();

  // Очищаем поля в зависимости от выбранного метода доставки
  if (customerData.value.delivery_method === 'cdek') {
    customerData.value.delivery_address = '';
  } else {
    customerData.value.delivery_city = '';
    customerData.value.delivery_pickup_point = '';
    selectedCdekCityCode.value = '';
    selectedCdekPickupPointCode.value = '';
  }
});

// Загрузка данных при монтировании компонента
onMounted(async () => {
  try {
    await cartStore.fetchCartProducts();
  } catch (error) {
    console.error('Ошибка при загрузке корзины:', error);
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Не удалось загрузить корзину',
      life: 3000
    });
  }
});
</script>

<style scoped>
.cart-item {
  border: 1px solid #eee;
  padding: 15px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.m-auto {
  width: 100%;
  overflow: hidden; /* Предотвращает выход содержимого за границы */
}

.product-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
  position: relative; /* Добавить относительное позиционирование */
  z-index: 1; /* Убедиться, что изображение находится поверх других элементов */
}

.image-placeholder {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f0f0;
  color: #666;
  font-size: 12px;
  border-radius: 4px;
}

.summary-box {
  border: 1px solid #eee;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  background-color: #f9f9f9;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.summary-row.total {
  font-weight: bold;
  font-size: 1.1em;
  border-bottom: none;
}

.payment-success {
  padding: 20px;
  background-color: #d4edda;
  color: #155724;
  border-radius: 4px;
  margin-bottom: 20px;
  text-align: center;
}

.payment-error {
  padding: 20px;
  background-color: #f8d7da;
  color: #721c24;
  border-radius: 4px;
  margin-bottom: 20px;
}

.empty-cart {
  text-align: center;
  padding: 40px 20px;
}

.empty-cart-icon {
  font-size: 4rem;
  color: #ccc;
  margin-bottom: 20px;
}

.form-container {
  border: 1px solid #eee;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.form-group label {
  display: block;
}

.steps-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.step-connector {
  flex-grow: 1;
  height: 2px;
  background-color: #e0e0e0;
  margin: 0 10px;
}

.step-number {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 5px;
}

.step.active .step-number {
  background-color: #007bff;
  color: white;
}

.step-text {
  font-size: 14px;
}

.step.active .step-text {
  font-weight: bold;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  cursor: pointer; /* Добавляет курсор-указатель при наведении */
  transition: all 0.3s ease; /* Плавный переход для эффектов при наведении */
}

.step:hover {
  opacity: 0.8; /* Небольшое изменение прозрачности при наведении */
}

/* Если вы хотите, чтобы неактивные шаги были недоступны для клика */
.step.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.cart-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.checkout-steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.summary-box {
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.empty-cart {
  text-align: center;
  padding: 50px 0;
}

.empty-cart-icon {
  font-size: 3rem;
  color: #ccc;
  margin-bottom: 20px;
}

.cart-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.cart-item-image {
  width: 80px;
  height: 80px;
  margin-right: 15px;
  border-radius: 4px;
  display: flex; /* Изменить на flex */
  justify-content: center; /* Центрирование по горизонтали */
  align-items: center; /* Центрирование по вертикали */
  overflow: hidden; /* Обрезать выходящее за границы содержимое */
  position: relative; /* Для абсолютного позиционирования внутренних элементов */
}

.cart-item-details {
  flex: 1;
}

.cart-item-actions {
  display: flex;
  align-items: center;
}

.quantity-control {
  display: flex;
  align-items: center;
  margin-right: 15px;
}

.quantity-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f0f0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.quantity-input {
  width: 40px;
  text-align: center;
  margin: 0 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 5px;
}

.cart-summary {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.error-message {
  color: #f44336;
  font-size: 0.8rem;
  margin-top: 5px;
}

[v-if="currentStep === 'confirmation'"] {
  color: #000 !important;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
}

/* Стили для блоков с белым фоном */
.order-summary,
.customer-info,
.summary-box {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
  color: #000 !important; /* Принудительно устанавливаем черный цвет текста */
}

/* Стили для заголовков */
.order-summary h2,
.order-summary h3,
.customer-info h2,
.customer-info h3 {
  color: #000 !important;
  margin-bottom: 15px;
}

/* Стили для текста внутри блоков */
.order-summary p,
.order-summary div,
.order-summary span,
.customer-info p,
.customer-info div,
.customer-info span {
  color: #000 !important;
}

/* Стили для разделителей */
.order-summary hr,
.customer-info hr {
  border-color: #ddd;
  margin: 15px 0;
}

/* Стили для общей суммы */
.font-weight-bold {
  font-weight: bold;
  color: #000 !important;
}

/* Стили для сообщений об ошибках (сохраняем красный цвет) */
.text-danger {
  color: #dc3545 !important;
}

/* Общие стили для шага подтверждения */
[v-if="currentStep === 'confirmation'"] h2 {
  color: #000 !important;
  margin-bottom: 20px;
}

/* Стили для информации о товарах */
[v-if="currentStep === 'confirmation'"] .d-flex {
  color: #000 !important;
}

/* Стили для кнопок на шаге подтверждения */
[v-if="currentStep === 'confirmation'"] .navigation-buttons {
  margin-top: 20px;
}

.shipping-error-container {
  background-color: rgba(220, 53, 69, 0.1);
  border-left: 3px solid #dc3545;
  padding: 10px 15px;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #000 !important;
}

.shipping-error-message {
  display: flex;
  align-items: center;
  color: #000 !important;
}

.shipping-error-message i {
  margin-right: 8px;
  color: #dc3545;
}

.shipping-error-message span {
  color: #000 !important;
  font-size: 0.9rem;
}

.cart-page-wrapper {
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.delivery-options {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.delivery-option {
  display: flex;
  align-items: center;
  gap: 10px;
}

.delivery-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  transition: all 0.3s;
}

.delivery-label:hover {
  border-color: #aaa;
}

.delivery-logo {
  width: 80px;
  height: auto;
  margin-bottom: 10px;
}

/* Стиль для выбранного метода доставки */
.delivery-option input:checked + .delivery-label {
  border-color: #2196F3;
  background-color: rgba(33, 150, 243, 0.1);
}

@media (max-width: 768px) {
  /* Общие контейнеры */
  .cart-page-wrapper {
    padding: 10px;
  }

  /* Шаги */
  .steps-container {
    flex-direction: column;
    align-items: stretch;
  }

  .step {
    flex-direction: row;
    justify-content: flex-start;
    margin-bottom: 10px;
  }

  .step-connector {
    display: none;
  }

  .step-number {
    margin-right: 10px;
    margin-bottom: 0;
  }

  /* Корзина */
  .cart-step {
    flex-direction: column;
  }

  .cart-items, .cart-summary {
    width: 100% !important;
    padding: 0 !important;
  }

  .cart-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .cart-item-image {
    margin-bottom: 10px;
    align-self: center;
  }

  /* Доставка */
  .delivery-options {
    flex-direction: column;
    gap: 10px;
  }

  .delivery-label {
    flex-direction: row;
    justify-content: flex-start;
    align-items: center;
  }

  .delivery-logo {
    width: 50px;
    margin-right: 10px;
    margin-bottom: 0;
  }

  /* Подтверждение заказа */
  .order-summary, .customer-info {
    padding: 15px;
  }

  /* Кнопки */
  .p-button {
    width: 100%;
  }

  /* Типографика */
  h1 {
    font-size: 1.5rem;
  }

  h2 {
    font-size: 1.3rem;
  }

  h3 {
    font-size: 1.1rem;
  }

  /* Поля ввода */
  .p-inputtext, .p-dropdown {
    width: 100%;
  }

  /* Адаптивность изображений */
  .product-image, .cart-item-image img {
    max-width: 100%;
    height: auto;
  }
}

@media (max-width: 480px) {
  .cart-page-wrapper {
    padding: 5px;
  }

  .steps-container {
    margin-bottom: 10px;
  }

  .step-text {
    font-size: 0.8rem;
  }

  .summary-box {
    padding: 10px;
  }

  .summary-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-row span {
    margin-bottom: 5px;
  }
}

/* Стили для кнопок выбора способа доставки */
.delivery-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.delivery-label {
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 56px; /* Фиксированная высота для обеих кнопок */
  padding: 0 15px;
  border: 1px solid #333;
  border-radius: 8px;
  transition: all 0.3s;
  width: 100%;
  justify-content: flex-start;
}

.delivery-logo {
  height: 32px; /* Фиксированная высота для логотипов */
  width: auto;
  margin-right: 10px;
  margin-bottom: 0;
  object-fit: contain;
}

/* Стиль для выбранного метода доставки */
.delivery-option input:checked + .delivery-label {
  border-color: #2196F3;
  background-color: rgba(33, 150, 243, 0.1);
}

/* Медиа-запрос для мобильных устройств */
@media (max-width: 768px) {
  .delivery-label {
    height: 56px; /* Сохраняем ту же высоту на мобильных */
  }
}

.pole {
  margin-top: 8px
}

/* Стили для хедера */
.header-full-width {
  width: 100%;
  background-color: var(--surface-section);
  border-bottom: 1px solid var(--surface-border);
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.brand-name {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-color);
  margin: 0;
}

.brand-link {
  text-decoration: none;
  color: inherit;
}

/* Контейнер для кнопок в хедере */
.header-buttons {
  display: flex;
  gap: 0.5rem;
}

/* Стиль для кнопок */
.home-button,
.cart-button {
  width: 3rem !important;
  height: 3rem !important;
  font-size: 1.2rem !important;
}

/* Контейнер для контента */
.content-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
}

/* Стили для футера */
.footer {
  width: 100%;
  background-color: var(--surface-section);
  border-top: 1px solid var(--surface-border);
  margin-top: 2rem;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.footer-links {
  margin-bottom: 1rem;
  display: flex;
  gap: 1.5rem;
}

.footer-link {
  color: var(--text-color);
  text-decoration: none;
  transition: color 0.3s ease;
  font-size: 0.9rem;
}

.footer-link:hover {
  color: var(--primary-color);
  text-decoration: underline;
}

.footer-copyright {
  color: var(--text-color-secondary);
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .header-container {
    padding: 1rem;
  }

  .brand-name {
    font-size: 2rem;
  }

  .footer-container {
    padding: 1.5rem 1rem;
  }
}
/* Сброс отступов для страницы корзины */
.cart-page {
  margin: 0;
  padding: 0;
  width: 100%;
}

/* Применяем стили к body только когда активна страница корзины */
:global(body) {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}
@media (max-width: 768px) {
  .footer-links {
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
}
</style>