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
          <li v-for="item in cartStore.insufficientItems" :key="item.id">
            {{ item.name }} - запрошено: {{ item.requested }}, доступно: {{ item.available }}
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
          <h3>Информация о доставке</h3>

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
                    :validation-rules="{ required: helpers.withMessage('Пожалуйста, введите адрес доставки', required) }"
                    @address-normalized="handleAddressNormalized"
                />
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

              <!-- Отображение информации о нормализованном адресе -->
              <div v-if="normalizedAddressInfo" class="p-col-12 mt-3">
                <div class="p-card p-3"
                     :class="{ 'address-valid': normalizedAddressInfo.is_valid, 'address-invalid': !normalizedAddressInfo.is_valid }">
                  <h4>Информация о доставке:</h4>
                  <div class="address-details">
                    <div class="detail-row">
                      <span class="detail-label">Почтовый индекс:</span>
                      <span class="detail-value">{{ normalizedAddressInfo.postal_code || 'Не определен' }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Регион:</span>
                      <span class="detail-value">{{ normalizedAddressInfo.details.region || 'Не определен' }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Город/Населенный пункт:</span>
                      <span class="detail-value">{{ normalizedAddressInfo.details.place || 'Не определен' }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Улица:</span>
                      <span class="detail-value">{{ normalizedAddressInfo.details.street || 'Не определена' }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Дом:</span>
                      <span class="detail-value">
                  {{ normalizedAddressInfo.details.house || 'Не определен' }}
                  {{ normalizedAddressInfo.details.corpus ? `корп. ${normalizedAddressInfo.details.corpus}` : '' }}
                  {{ normalizedAddressInfo.details.building ? `стр. ${normalizedAddressInfo.details.building}` : '' }}
                  {{ normalizedAddressInfo.details.letter ? `лит. ${normalizedAddressInfo.details.letter}` : '' }}
                </span>
                    </div>
                    <div class="detail-row" v-if="normalizedAddressInfo.details.room">
                      <span class="detail-label">Квартира/Офис:</span>
                      <span class="detail-value">{{ normalizedAddressInfo.details.room }}</span>
                    </div>
                  </div>

                  <div class="quality-info mt-2"
                       :class="{ 'quality-good': normalizedAddressInfo.is_valid, 'quality-bad': !normalizedAddressInfo.is_valid }">
                    <i :class="normalizedAddressInfo.is_valid ? 'pi pi-check-circle' : 'pi pi-exclamation-triangle'"></i>
                    <span>{{ normalizedAddressInfo.quality.description }}</span>
                  </div>

                  <div v-if="!normalizedAddressInfo.is_valid" class="warning-message mt-2">
                    <i class="pi pi-info-circle"></i>
                    <span>Пожалуйста, проверьте адрес и уточните детали для корректной доставки.</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="button-row mt-4">
              <Button type="button" @click="goToCart" label="Назад" class="p-button-outlined mr-2"/>
              <Button type="submit" label="Продолжить" :disabled="!canProceedToConfirmation"/>
            </div>
          </form>
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
</template>

<script setup>
import { ref, computed } from 'vue';
import { useCart } from '~/composables/useCart.js';
import { useVuelidate } from '@vuelidate/core';
import { required, email, helpers } from '@vuelidate/validators';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Button from 'primevue/button';
import AddressNormalizer from '~/components/AddressNormalizer.vue';

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

const normalizedAddressInfo = ref(null);

const goToCart = () => {
  // Проверка, чтобы предотвратить ненужные переходы, если пользователь уже на этом шаге
  if (currentStep.value !== 'cart') {
    currentStep.value = 'cart';
  }
};


const goToConfirmation = () => {
  // Проверка валидности данных доставки перед переходом к подтверждению
  if (v$.value.$valid) {
    currentStep.value = 'confirmation';
  } else {
    // Показать сообщение об ошибке или выполнить валидацию
    v$.value.$touch();
    // Можно добавить уведомление пользователю
    // toast.error('Пожалуйста, заполните все обязательные поля');
  }
};
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

const v$ = useVuelidate(rules, customerData);

// Функции
const home = () => {
  router.push('/');
};
// asd
const removeItem = async (productId) => {
  await cartStore.removeFromCart(productId);
};


const goToDelivery = () => {
  currentStep.value = 'delivery';
};

const confirmOrder = async () => {
  // Валидация формы
  const isFormValid = await v$.value.$validate();
  if (!isFormValid) {
    return;
  }

  const canProceedToConfirmation = computed(() => {
  // Базовая проверка валидности формы
  if (v$.value.$invalid) return false;

  // Дополнительная проверка: если адрес был нормализован, но не валиден,
  // показываем предупреждение, но всё равно позволяем продолжить
  if (normalizedAddressInfo.value && !normalizedAddressInfo.value.is_valid) {
    // Можно добавить дополнительную логику здесь
    // Например, требовать подтверждения от пользователя
    return true;
  }

  return true;
});

// Обработчик события нормализации адреса
function handleAddressNormalized(result) {
  normalizedAddressInfo.value = result;

  // Сохраняем почтовый индекс для дальнейшего использования при расчете доставки
  if (result.postal_code) {
    // Можно сохранить в отдельное поле или в локальное хранилище
    localStorage.setItem('delivery_postal_code', result.postal_code);
  }
}

function goToCart() {
  currentStep.value = 'cart';
}

function goToConfirmation() {
  // Проверка валидности данных доставки перед переходом к подтверждению
  if (v$.value.$valid) {
    currentStep.value = 'confirmation';
  } else {
    // Показать сообщение об ошибке или выполнить валидацию
    v$.value.$touch();
    // Можно добавить уведомление пользователю
    // toast.error('Пожалуйста, заполните все обязательные поля');
  }
}


  // Отправка заказа на сервер
  await cartStore.processPayment(customerData.value);

  // Если оплата прошла успешно, показываем подтверждение
  if (cartStore.paymentStatus === 'success') {
    currentStep.value = 'confirmation';
  }
};

onMounted(async () => {
  await cartStore.fetchCartProducts();
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