<template>
  <div class="payment-result-page">
    <div class="header-full-width">
      <div class="header-container">
        <div class="brand-link" @click="goToHome">
          <h1 class="brand-name">Voshod</h1>
        </div>
        <div class="header-buttons">
          <Button @click="goToHome" class="p-button-primary home-button" icon="pi pi-home" tooltip="На главную"
                  tooltipOptions="{position: 'bottom'}"/>
        </div>
      </div>
    </div>

    <div class="content-container">
      <div v-if="loading" class="loading-container">
        <ProgressSpinner />
        <p>Проверяем статус платежа...</p>
      </div>

      <div v-else-if="paymentResult" class="payment-result">
        <div v-if="paymentResult.status === 'success'" class="payment-success">
          <i class="pi pi-check-circle success-icon"></i>
          <h2>Платеж успешно завершен!</h2>
          <p>Спасибо за ваш заказ. Мы начнем обработку заказа в ближайшее время.</p>
          <p v-if="orderDetails">Номер вашего заказа: <strong>{{ orderDetails.id }}</strong></p>
          <p>Информация о заказе была отправлена на ваш email.</p>
          <Button @click="goToHome" label="Вернуться на главную" class="mt-3"/>
        </div>

        <div v-else-if="paymentResult.status === 'error'" class="payment-error">
          <i class="pi pi-times-circle error-icon"></i>
          <h2>Ошибка при обработке платежа</h2>
          <p>{{ paymentResult.message || 'Произошла ошибка при обработке платежа' }}</p>
          <p>Пожалуйста, попробуйте оформить заказ еще раз или свяжитесь с нами для получения помощи.</p>
          <Button @click="goToCart" label="Вернуться к корзине" class="mt-3"/>
        </div>

        <div v-else-if="paymentResult.status === 'pending'" class="payment-pending">
          <i class="pi pi-clock pending-icon"></i>
          <h2>Платеж в обработке</h2>
          <p>Ваш платеж обрабатывается. Пожалуйста, подождите или проверьте статус позже.</p>
          <p v-if="orderDetails">Номер вашего заказа: <strong>{{ orderDetails.id }}</strong></p>
          <div class="button-group">
            <Button @click="checkPayment" label="Проверить статус" class="mt-3 mr-2"/>
            <Button @click="goToHome" label="Вернуться на главную" class="mt-3"/>
          </div>
        </div>
      </div>

      <div v-else class="payment-unknown">
        <i class="pi pi-question-circle unknown-icon"></i>
        <h2>Информация о платеже отсутствует</h2>
        <p>Не удалось получить информацию о вашем платеже.</p>
        <div class="button-group">
          <Button @click="goToCart" label="Перейти в корзину" class="mt-3 mr-2"/>
          <Button @click="goToHome" label="Вернуться на главную" class="mt-3"/>
        </div>
      </div>
    </div>

    <!-- Футер -->
    <div class="footer">
      <div class="footer-container">
        <div class="footer-links">
          <span class="footer-link" @click="goToHome">Главная</span>
          <span class="footer-link" @click="goToOffer">Публичная оферта</span>
          <span class="footer-link" @click="goToContacts">Контакты</span>
        </div>
        <div class="footer-copyright">
          © 2023 Voshod. Все права защищены.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useCart } from '~/composables/useCart.js';
import { useToast } from 'primevue/usetoast';
import Button from 'primevue/button';
import ProgressSpinner from 'primevue/progressspinner';

const toast = useToast();
const cartStore = useCart();

const loading = ref(true);
const paymentResult = ref(null);
const orderDetails = ref(null);

// Функции для навигации
const goToHome = () => {
  window.location.href = '/';
};

const goToCart = () => {
  window.location.href = '/cart';
};

const goToOffer = () => {
  window.location.href = '/offer';
};

const goToContacts = () => {
  window.location.href = '/contacts';
};

// Функция для проверки статуса платежа
async function checkPayment() {
  loading.value = true;

  try {
    const result = await cartStore.checkPaymentResult();
    if (result) {
      paymentResult.value = result;

      // Показываем уведомление в зависимости от статуса
      if (result.status === 'success') {
        toast.add({
          severity: 'success',
          summary: 'Успех',
          detail: 'Платеж успешно завершен!',
          life: 3000
        });
      } else if (result.status === 'error') {
        toast.add({
          severity: 'error',
          summary: 'Ошибка',
          detail: result.message || 'Произошла ошибка при обработке платежа',
          life: 5000
        });
      } else if (result.status === 'pending') {
        toast.add({
          severity: 'info',
          summary: 'Информация',
          detail: 'Платеж все еще обрабатывается',
          life: 3000
        });
      }
    }
  } catch (error) {
    console.error('Ошибка при проверке статуса платежа:', error);
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Произошла ошибка при проверке статуса платежа',
      life: 5000
    });
  } finally {
    loading.value = false;
  }
}

// Проверка результата платежа при загрузке страницы
onMounted(async () => {
  try {
    // Получаем параметры из URL
    const urlParams = new URLSearchParams(window.location.search);
    const paymentId = urlParams.get('payment_id');
    const orderId = urlParams.get('order_id');

    // Если есть ID платежа в URL, используем его для проверки
    if (paymentId && orderId) {
      // Здесь можно добавить прямой запрос к API для проверки статуса платежа
      const response = await fetch('/api/check-payment-status/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ order_id: orderId })
      });

      const data = await response.json();

      if (data.status === 'success') {
        paymentResult.value = {
          status: data.payment_status === 'succeeded' ? 'success' :
                 data.payment_status === 'canceled' ? 'error' : 'pending',
          message: data.payment_status === 'succeeded' ? 'Платеж успешно завершен' :
                  data.payment_status === 'canceled' ? 'Платеж отменен' : 'Платеж в обработке'
        };

        // Сохраняем детали заказа
        orderDetails.value = { id: orderId };
      } else {
        paymentResult.value = {
          status: 'error',
          message: data.message || 'Ошибка при проверке статуса платежа'
        };
      }
    } else {
      // Иначе используем данные из localStorage
      const result = await cartStore.checkPaymentResult();
      paymentResult.value = result;

      // Если есть данные о текущем платеже в localStorage
      const paymentDataStr = localStorage.getItem('currentPayment');
      if (paymentDataStr) {
        const paymentData = JSON.parse(paymentDataStr);
        orderDetails.value = { id: paymentData.orderId };
      }
    }
  } catch (error) {
    console.error('Ошибка при проверке результата платежа:', error);
    paymentResult.value = {
      status: 'error',
      message: 'Произошла ошибка при проверке статуса платежа'
    };
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.payment-result-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.content-container {
  flex: 1;
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.payment-result {
  width: 100%;
  max-width: 600px;
  padding: 2rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.payment-success {
  background-color: #d4edda;
  color: #155724;
}

.payment-error {
  background-color: #f8d7da;
  color: #721c24;
}

.payment-pending {
  background-color: #fff3cd;
  color: #856404;
}

.payment-unknown {
  width: 100%;
  max-width: 600px;
  padding: 2rem;
  border-radius: 8px;
  text-align: center;
  background-color: #e2e3e5;
  color: #383d41;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.success-icon,
.error-icon,
.pending-icon,
.unknown-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.success-icon {
  color: #28a745;
}

.error-icon {
  color: #dc3545;
}

.pending-icon {
  color: #ffc107;
}

.unknown-icon {
  color: #6c757d;
}

.button-group {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
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
  cursor: pointer;
}

.header-buttons {
  display: flex;
  gap: 0.5rem;
}

.home-button {
  width: 3rem !important;
  height: 3rem !important;
  font-size: 1.2rem !important;
}

/* Стили для футера */
.footer {
  width: 100%;
  background-color: var(--surface-section);
  border-top: 1px solid var(--surface-border);
  margin-top: auto;
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
  cursor: pointer;
}

.footer-link:hover {
  color: var(--primary-color);
  text-decoration: underline;
}

.footer-copyright {
  color: var(--text-color-secondary);
  font-size: 0.85rem;
}

/* Адаптивные стили */
@media (max-width: 768px) {
  .header-container {
    padding: 1rem;
  }

  .brand-name {
    font-size: 2rem;
  }

  .payment-result,
  .payment-unknown {
    padding: 1.5rem;
  }

  .footer-container {
    padding: 1.5rem 1rem;
  }

  .footer-links {
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .button-group {
    flex-direction: column;
  }

  .button-group .p-button {
    margin-right: 0 !important;
    margin-bottom: 0.5rem;
  }
}
</style>