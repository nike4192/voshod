<template>
  <div class="flex justify-content-between flex-wrap">
    <h1>{{ currentStep === 'cart' ? 'Товары в корзине' : 'Оформление заказа' }}</h1>
    <Button @click="home" style="width:50px; height:50px;" icon="pi pi-home"></Button>
  </div>
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
            {{ insufficientItem.name }} - запрошено: {{ insufficientItem.requested }}, доступно: {{ insufficientItem.available }}
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
                <div class="p-col-12">
                  <!-- Интеграция компонента AddressNormalizer -->
                  <AddressNormalizer
                      v-model="customerData.delivery_address"
                      :error="v$.delivery_address.$invalid && v$.delivery_address.$dirty"
                      ref="addressNormalizerRef"
                      @blur="validateAddress"
                  />
                  <small v-if="v$.delivery_address.$invalid && v$.delivery_address.$dirty" class="p-error">
                    {{ v$.delivery_address.$errors[0].$message }}
                  </small>
                </div>
                <div class="p-col-12">
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
                <Button label="Назад к корзине" @click="goToCart" outlined />
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
  <div v-if="currentStep === 'cart'" class="cart-summary mt-3">
    <div class="flex justify-content-between">
      <span class="font-bold">Общий вес:</span>
      <span>{{ cartStore.totalWeight.toFixed(2) }} кг</span>
    </div>
  </div>
  <!-- Шаг 3: Подтверждение -->
  <div v-if="currentStep === 'confirmation'" class="confirmation-step">
    <h2>Подтверждение заказа</h2>
    <!-- Информация о заказе -->
    <div class="order-summary">
      <h3>Данные заказа</h3>
      <div class="customer-info">
        <p><strong>Имя:</strong> {{ customerData.customer_name }}</p>
        <p><strong>Email:</strong> {{ customerData.customer_email }}</p>
        <p><strong>Телефон:</strong> {{ customerData.customer_phone }}</p>
        <p><strong>Адрес доставки:</strong> {{ customerData.delivery_address }}</p>
      </div>
      <h3>Товары в корзине</h3>
      <div v-for="cartItem in cartStore.cartProducts" :key="cartItem.id" class="cart-item">
        <p>{{ cartItem.name }} - {{ cartItem.quantity }} шт. x {{ cartItem.price }} руб.</p>
      </div>
      <div class="order-total">
        <p><strong>Итого:</strong> {{ cartStore.totalPrice }} руб.</p>
      </div>
    </div>
    <!-- Кнопки навигации -->
    <div class="navigation-buttons">
      <Button label="Назад к доставке" class="p-button-secondary" @click="currentStep = 'delivery'" />
      <Button label="Подтвердить заказ" class="p-button-success" @click="confirmOrder" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useCart } from '~/composables/useCart.js';
import { useVuelidate } from '@vuelidate/core';
import { required, email, helpers } from '@vuelidate/validators';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Button from 'primevue/button';
import ProgressSpinner from 'primevue/progressspinner';
import AddressNormalizer from '~/components/AddressNormalizer.vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';

const toast = useToast();
const router = useRouter();
const cartStore = useCart();

// Текущий шаг оформления заказа
const currentStep = ref('cart');

// Данные покупателя
const customerData = ref({
  customer_name: '',
  customer_email: '',
  customer_phone: '',
  delivery_address: '',
  delivery_comment: ''
});

// Правила валидации
const rules = {
  customer_name: { required: helpers.withMessage('Пожалуйста, введите ваше имя', required) },
  customer_email: {
    required: helpers.withMessage('Пожалуйста, введите ваш email', required),
    email: helpers.withMessage('Пожалуйста, введите корректный email', email)
  },
  customer_phone: { required: helpers.withMessage('Пожалуйста, введите ваш телефон', required) },
  delivery_address: { required: helpers.withMessage('Пожалуйста, введите адрес доставки', required) }
};

// Инициализация Vuelidate
const v$ = useVuelidate(rules, customerData);

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

// Функция для перехода к шагу "Подтверждение"
const goToConfirmation = async () => {
  console.log('Вызвана функция goToConfirmation');

  try {
    // Запускаем валидацию
    const isValid = await v$.value.$validate();
    console.log('v$.value.$valid:', isValid);

    if (isValid) {
      console.log('Форма валидна, переходим к подтверждению');
      currentStep.value = 'confirmation';
    } else {
      console.log('Форма не валидна, показываем ошибки');
      toast.add({
        severity: 'error',
        summary: 'Ошибка',
        detail: 'Пожалуйста, заполните все обязательные поля корректно',
        life: 3000
      });
    }
  } catch (error) {
    console.error('Ошибка при валидации формы:', error);
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Произошла ошибка при валидации формы',
      life: 3000
    });
  }
};

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
const confirmOrder = async () => {
  try {
    // Подготавливаем данные для отправки
    const orderData = {
      customer_name: customerData.value.customer_name,
      customer_email: customerData.value.customer_email,
      customer_phone: customerData.value.customer_phone,
      delivery_address: customerData.value.delivery_address,
      delivery_comment: customerData.value.delivery_comment || ''
    };

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

      // Очищаем форму
      customerData.value = {
        customer_name: '',
        customer_email: '',
        customer_phone: '',
        delivery_address: '',
        delivery_comment: ''
      };

      // Переход на главную страницу
      setTimeout(() => {
        router.push('/');
      }, 2000);
    } else {
      // Обработка ошибки
      const errorMessage = result && result.message ? result.message : 'Произошла ошибка при оформлении заказа';
      toast.add({
        severity: 'error',
        summary: 'Ошибка',
        detail: errorMessage,
        life: 3000
      });
    }
  } catch (error) {
    console.error('Ошибка при оформлении заказа:', error);
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Произошла ошибка при оформлении заказа',
      life: 3000
    });
  }
};

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

.product-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
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

</style>