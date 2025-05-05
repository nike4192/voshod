<template>
  <div class="page-wrapper">
    <!-- Шапка на всю ширину -->
    <div class="header-full-width">
      <div class="header-container">
        <NuxtLink to="/" class="brand-link">
          <h1 class="brand-name">Voshod</h1>
        </NuxtLink>
        <div class="header-buttons">
          <Button @click="goToHome" class="p-button-primary home-button" icon="pi pi-home" tooltip="На главную" tooltipOptions="{position: 'bottom'}" />
          <Button @click="basket" class="p-button-primary cart-button" icon="pi pi-shopping-cart" tooltip="Корзина" tooltipOptions="{position: 'bottom'}" />
        </div>
      </div>
    </div>

    <!-- Контейнер для контента контактов -->
    <div class="content-container contacts-container">
      <h1 class="contacts-title">Контакты</h1>

      <div class="contacts-content">
        <div class="contact-section personal-info">
          <h2>Самозанятый</h2>
          <p><strong>ФИО:</strong> Черепанов Данила Вячеславович</p>
          <p><strong>Телефон:</strong> <a href="tel:+79222151505" class="contact-link">+7 (922) 215-15-05</a></p>
          <p><strong>Email:</strong> <a href="mailto:wocxod.vshd@yandex.ru"
                                        class="contact-link">wocxod.vshd@yandex.ru</a></p>
        </div>

        <div class="contact-section bank-info">
          <h2>Банковские реквизиты</h2>
          <div class="bank-details">
            <p><strong>Валюта получаемого перевода:</strong> Российский рубль (RUB)</p>
            <p><strong>Получатель:</strong> ЧЕРЕПАНОВ ДАНИЛА ВЯЧЕСЛАВОВИЧ</p>
            <p><strong>Номер счёта:</strong> 40817810016546911542</p>
            <p><strong>Банк получателя:</strong> УРАЛЬСКИЙ БАНК ПАО СБЕРБАНК</p>
            <p><strong>БИК:</strong> 046577674</p>
            <p><strong>Корр. счёт:</strong> 30101810500000000674</p>
            <p><strong>ИНН:</strong> 7707083893</p>
            <p><strong>КПП:</strong> 665843001</p>
            <p><strong>ОКПО:</strong> 02813463</p>
            <p><strong>ОГРН:</strong> 1027700132195</p>
            <p><strong>SWIFT-код:</strong> SABRRUMMEA1</p>
            <p><strong>Почтовый адрес банка:</strong> 620014, ЕКАТЕРИНБУРГ, УЛ. БОРИСА ЕЛЬЦИНА, Д. 3/2</p>
            <p><strong>Почтовый адрес доп.офиса:</strong> 620075, Г. ЕКАТЕРИНБУРГ, ПР-Т. ЛЕНИНА, 48</p>
          </div>
        </div>

        <div class="contact-section social-media">
          <h2>Социальные сети</h2>
          <div class="social-links">
            <a href="https://vk.com/wocxod" target="_blank" class="social-link">
              <span class="social-icon vk-icon">VK</span>
              <span>ВКонтакте</span>
            </a>
            <a href="https://t.me/w0cxod" target="_blank" class="social-link">
              <i class="pi pi-send"></i>
              <span>Telegram</span>
            </a>
            <a href="https://www.youtube.com/@-wocxod-" target="_blank" class="social-link">
              <i class="pi pi-youtube"></i>
              <span>YouTube</span>
            </a>
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
import { useRouter } from 'vue-router';

const router = useRouter();

const goToHome = () => {
  router.push('/');
};

const basket = () => {
  router.push('/cart');
};
</script>

<style>
/* Сброс отступов для страницы */
.page-wrapper {
  margin: 0;
  padding: 0;
  width: 100%;
}

/* Применяем стили к body */
body {
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

/* Контейнер для центрированного контента */
.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

/* Стили для страницы контактов */
.contacts-container {
  max-width: 900px;
}

.contacts-title {
  text-align: center;
  margin-bottom: 2rem;
  font-size: 2rem;
  font-weight: 600;
}

.contacts-content {
  line-height: 1.6;
}

.contact-section {
  margin-bottom: 2.5rem;
  padding: 1.5rem;
  background-color: var(--surface-card);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.contact-section h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 1px solid var(--surface-border);
  padding-bottom: 0.5rem;
}

.contact-section p {
  margin-bottom: 0.7rem;
}

.bank-details {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.5rem;
}

.social-links {
  display: flex;
  gap: 1.5rem;
  margin-top: 1rem;
}

.social-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--text-color);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background-color: var(--surface-hover);
  transition: all 0.3s ease;
}

.social-link:hover {
  background-color: var(--primary-color);
  color: var(--primary-color-text);
}

.social-link i {
  font-size: 1.2rem;
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

/* Адаптивность для мобильных устройств */
@media (max-width: 768px) {
  .brand-name {
    font-size: 2rem;
  }

  .header-container {
    padding: 1rem;
  }

  .contacts-title {
    font-size: 1.7rem;
  }

  .contact-section h2 {
    font-size: 1.3rem;
  }

  .bank-details {
    grid-template-columns: 1fr;
  }

  .social-links {
    flex-direction: column;
    gap: 1rem;
  }

  .footer-container {
    padding: 1.5rem 1rem;
  }

  .footer-links {
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
}
/* Стили для социальных иконок */
.social-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  font-size: 0.9rem;
  font-weight: bold;
}

.vk-icon {
  background-color: #4C75A3;
  color: white;
  border-radius: 4px;
}

/* Обновленные стили для социальных ссылок */
.social-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
}

.social-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--text-color);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background-color: var(--surface-hover);
  transition: all 0.3s ease;
  min-width: 140px;
}

.social-link:hover {
  background-color: var(--primary-color);
  color: var(--primary-color-text);
}

.social-link i {
  font-size: 1.2rem;
}

/* Специфические стили для YouTube */
.social-link .pi-youtube {
  color: #FF0000;
}

.social-link:hover .pi-youtube {
  color: inherit;
}
</style>