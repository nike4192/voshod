<template>
  <div class="flex justify-content-between flex-wrap">
    <h1>Товары в корзине</h1>
    <Button @click="home" style="width:50px; height:50px;" icon="pi pi-home"></Button>
  </div>
  <!-- Сообщения об ошибках или успешной оплате -->
  <div v-if="cartStore.paymentStatus === 'success'" class="payment-success">
    {{ cartStore.paymentMessage }}
    <Button @click="home" label="Вернуться на главную" class="mt-3"/>
  </div>

  <div v-else-if="cartStore.paymentStatus === 'error'" class="payment-error">
    <h3>{{ cartStore.paymentMessage }}</h3>

    <div v-if="cartStore.insufficientItems.length > 0" class="mt-3">
      <h4>Недостаточно товаров на складе:</h4>
      <ul>
        <li v-for="item in cartStore.insufficientItems" :key="item.id">
          {{ item.name }} - запрошено: {{ item.requested }}, доступно: {{ item.available }}
        </li>
      </ul>
    </div>
  </div>


  <div v-if="cartStore.loading">Загрузка...</div>
  <div v-else>
    <div v-if="cartStore.cartProducts.length === 0">Корзина пуста</div>
    <div v-else>
      <div class="flex">
        <div style="width:800px">
          <div v-for="item in cartStore.cartProducts" :key="item.id"
               class="flex flex-row flex-wrap cart-item border-round-lg w-full align-items-center">
            <div class="cart-item-image mr-3 " style="width:128px; higth:128px">
              <img v-if="item.image_url" :src="item.image_url" :alt="item.name" class="product-image w-full"
              />
              <div v-else class="image-placeholder">Нет изображения</div>
            </div>

            <div class="cart-item-details flex-grow-1">
              <h2 class="mx-5">{{ item.name }}</h2>
              <p>Цена: {{ item.price }}</p>
              <p class="mx-5">Количество: {{ item.quantity }}</p>
            </div>

            <Button
                @click="removeItem(item.id)"
                class="p-button-danger p-button-sm"
                icon="pi pi-trash"
                :disabled="cartStore.loading"
            ></Button>
          </div>
        </div>
        <div>
          <div class="p-4 border-round-lg cart-summary">
            <h3>Итого:</h3>
            <p class="total-price">{{ cartStore.totalPrice }} руб.</p>
            <button class="p-4 mx-1" @click="checkout" :disabled="cartStore.loading">оплатить</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Добавьте это перед кнопкой оплаты -->
<div class="customer-form p-4 border-round-lg mb-3">
  <h3>Данные для оформления заказа</h3>
  <div class="form-group mb-2">
    <label for="customer_name">Имя:</label>
    <input
      id="customer_name"
      v-model="customerData.customer_name"
      class="w-full p-2"
      required
    />
  </div>
  <div class="form-group mb-2">
    <label for="customer_email">Email:</label>
    <input
      id="customer_email"
      type="email"
      v-model="customerData.customer_email"
      class="w-full p-2"
      required
    />
  </div>
  <div class="form-group mb-2">
    <label for="customer_phone">Телефон:</label>
    <input
      id="customer_phone"
      v-model="customerData.customer_phone"
      class="w-full p-2"
      required
    />
  </div>
</div>
</template>


<script setup>
import { onMounted } from "vue";
import { useCart } from "~/composables/useCart.js";
const router = useRouter();
const cartStore = useCart();

const checkout = async () => {
  // Здесь можно добавить валидацию данных покупателя, если нужно
  await cartStore.processPayment(customerData.value);
  // Если нужно, можно добавить перенаправление после успешной оплаты
  // if (cartStore.paymentStatus === 'success') {
  //   router.push('/order-success');
  // }
};

const customerData = ref({
  customer_name: '',
  customer_email: '',
  customer_phone: ''
});

const home = () => {
  router.push('/');
};

onMounted(async () => {
  await cartStore.fetchCartProducts();
});

const removeItem = async (productId) => {
  await cartStore.removeFromCart(productId);
};

</script>

<style scoped>
.cart-item {
  border: 1px solid #ccc;
  padding: 10px;
  margin-bottom: 10px;
}
</style>