<template>
<div class="index-page">
  <div>
    <!-- Шапка на всю ширину -->
    <div class="header-full-width">
      <div class="header-container">
        <h1 class="brand-name">Voshod</h1>
        <Button @click="basket" class="p-button-primary cart-button" icon="pi pi-shopping-cart" />
      </div>
    </div>

    <!-- Контейнер для центрированной сетки товаров -->
    <div class="content-container">
      <!-- Заголовок секции товаров -->
      <div class="section-title">
        <h2>Товары</h2>
      </div>

      <!-- Сетка товаров -->
      <div class="grid products-grid">
        <div v-for="product in products" :key="product.id" class="col-12 md:col-6 lg:col-4 product-card-wrapper">
          <Card class="product-card">
            <template #header>
              <div class="product-image-container">
                <img :src="product.image" class="product-image" />
              </div>
            </template>
            <template #title>
              <div class="product-name">{{ product.name }}</div>
            </template>
            <template #subtitle>
              <div class="product-price">{{ product.price }} &#8381;</div>
            </template>
            <template #content>
              <p class="product-description m-0"></p>
              <div class="stock-info">
                <span :class="{'stock-low': product.stock < 5}">В наличии: {{ product.stock }} шт.</span>
              </div>
            </template>
            <template #footer>
              <div class="product-actions">
                <Button 
                  label="В корзину" 
                  class="p-button-outlined" 
                  @click="addToCart(product)"
                  :disabled="product.stock <= 0"
                />
              </div>
            </template>
          </Card>
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
</div>
</template>

<script setup>
import {useProducts} from '~/composables/useProduct.js';
import {useCart} from '~/composables/useCart.js';
import {ref, onMounted, onUnmounted} from 'vue';
import { useToast } from 'primevue/usetoast';

const products = ref([]);
const error = ref(null);
const router = useRouter();
const cartStore = useCart();
const toast = useToast();

// Добавляем класс к body при монтировании компонента
onMounted(() => {
  document.body.classList.add('index-page-active');
});

// Удаляем класс при размонтировании компонента
onUnmounted(() => {
  document.body.classList.remove('index-page-active');
});

const basket = () => {
  router.push('/cart');
};

const addToCart = async (product) => {
  if (product.stock <= 0) {
    toast.add({
      severity: 'warn',
      summary: 'Товар недоступен',
      detail: 'К сожалению, товара нет в наличии',
      life: 3000
    });
    return;
  }

  const result = await cartStore.addCart(product.id);
  
  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Успех',
      detail: 'Товар добавлен в корзину',
      life: 3000
    });
  } else if (result.error) {
    toast.add({
      severity: 'warn',
      summary: 'Ограничение количества',
      detail: result.message,
      life: 3000
    });
  }
};

onMounted(async () => {
  const productStore = await useProducts();
  await cartStore.fetchCartProducts();
  products.value = productStore.products;
  error.value = productStore.error;
})
</script>


<style>
/* Стили, адаптированные под тему Aura Dark Noir */
.index-page {
  margin: 0;
  padding: 0;
  width: 100%;
}

/* Применяем стили к body только когда активна страница index */
body.index-page-active {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

/* Шапка на всю ширину */
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

/* Более контрастная кнопка корзины */
.cart-button {
  width: 3rem !important;
  height: 3rem !important;
  font-size: 1.2rem !important;
}

/* Контейнер для центрированной сетки товаров */
.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.section-title {
  text-align: center;
  margin-bottom: 2rem;
}

.section-title h2 {
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--text-color);
}

.products-grid {
  margin: 0 -0.75rem;
}

.product-card-wrapper {
  padding: 0.75rem;
}

.product-card {
  height: 100%;
  background-color: var(--surface-card);
  border: 1px solid var(--surface-border);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  overflow: hidden;
}

/* Анимация увеличения при наведении */
.product-card:hover {
  transform: scale(1.03);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  z-index: 1;
}

.product-image-container {
  height: 0;
  padding-bottom: 100%; /* Квадратное соотношение сторон */
  position: relative;
  background-color: var(--surface-card); /* Фон такой же как у карточки */
  overflow: hidden;
}

/* Дополнительные стили для корректного отображения изображений */
:deep(.p-card-header) {
  padding: 0 !important;
  background-color: var(--surface-card) !important;
}

.product-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

/* Анимация увеличения изображения при наведении */
.product-card:hover .product-image {
  transform: scale(1.1);
}

.product-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
}

.product-price {
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-color-secondary);
}

.product-description {
  color: var(--text-color-secondary);
}

.product-actions {
  display: flex;
  justify-content: center;
  margin-top: 0.5rem;
}

.product-actions .p-button {
  width: 100%;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

/* Анимация кнопки при наведении */
.product-actions .p-button:hover {
  transform: translateY(-2px);
}

/* Адаптивность для мобильных устройств */
@media (max-width: 768px) {
  .brand-name {
    font-size: 2rem;
  }

  .section-title h2 {
    font-size: 1.5rem;
  }

  /* Уменьшаем эффект увеличения на мобильных устройствах */
  .product-card:hover {
    transform: scale(1.02);
  }

  .header-container {
    padding: 1rem;
  }
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
  .footer-container {
    padding: 1.5rem 1rem;
  }
}
@media (max-width: 768px) {
  .footer-links {
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
}

.stock-info {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.stock-low {
  color: #f59e0b;
}

.product-card .p-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>