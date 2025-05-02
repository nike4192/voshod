<template>
  <div class="address-normalizer">
    <!-- Десктопная версия -->
    <div v-if="!isMobile" class="desktop-view">
      <div class="p-field">
        <AutoComplete
          id="address"
          v-model="address"
          class="w-full dark-input"
          placeholder="Введите адрес доставки: Город, Улица, Дом"
          :suggestions="suggestions"
          @complete="searchAddress"
          @item-select="onAddressSelected"
          :dropdown="true"
          :class="{ 'p-invalid': hasError }"
          optionLabel="text"
          :loading="loading"
          appendTo="body"
        >
          <template #empty>
            <div class="p-2">Адреса не найдены</div>
          </template>
          <template #loader>
            <div class="p-2">Поиск адресов...</div>
          </template>
          <template #item="slotProps">
            <div>
              {{ slotProps.item.text }}
            </div>
          </template>
        </AutoComplete>
        <small v-if="hasError" class="p-error">
          Пожалуйста, введите адрес доставки
        </small>
      </div>
    </div>

    <!-- Мобильная версия -->
    <div v-else class="mobile-view">
      <div class="p-field position-relative">
        <div class="p-inputgroup">
          <InputText
            v-model="address"
            placeholder="Введите адрес доставки: Город, Улица, Дом"
            :class="{ 'p-invalid': hasError }"
            class="dark-input w-full"
            @input="onAddressInput"
          />
          <Button icon="pi pi-search" @click="showSuggestions = true" />
        </div>
        <small v-if="hasError" class="p-error">
          Пожалуйста, введите адрес доставки
        </small>

        <!-- Мобильный выпадающий список прикреплен к родительскому элементу -->
        <div v-if="showSuggestions && suggestions.length > 0" class="mobile-suggestions-container">
          <div
            v-for="(item, index) in suggestions"
            :key="index"
            class="suggestion-item p-2 cursor-pointer"
            @click="selectAddress(item)"
          >
            {{ item.text }}
          </div>
        </div>
      </div>

      <!-- Индикатор загрузки для мобильных -->
      <div v-if="loading && isMobile" class="loading-indicator">
        <ProgressSpinner style="width:30px;height:30px" />
        <span class="ml-2">Поиск...</span>
      </div>
    </div>

    <!-- Отображение информации о нормализованном адресе, если она есть -->
    <div v-if="normalizationResult && normalizationResult.status" class="normalization-result mt-2">
      <div v-if="normalizationResult.status === 'success'" class="success-message">
        <i class="pi pi-check-circle mr-2"></i>
        <small>Адрес успешно проверен</small>
      </div>
      <div v-else class="error-message">
        <i class="pi pi-exclamation-circle mr-2"></i>
        <small>{{ normalizationResult.message }}</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineEmits, defineProps, watch, computed, onMounted, onUnmounted } from 'vue';
import AutoComplete from 'primevue/autocomplete';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import ProgressSpinner from 'primevue/progressspinner';
import axios from 'axios';
import { useCart } from '~/composables/useCart.js';

const cartStore = useCart();
const formattedAddress = computed(() => {
  if (!normalizationResult.value || !normalizationResult.value.normalized_address) {
    return '';
  }
  return cartStore.formatAddress(normalizationResult.value.normalized_address);
});

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  error: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue', 'address-normalized']);
const address = ref(props.modelValue || '');
const normalizing = ref(false);
const loading = ref(false);
const normalizationResult = ref(null);
const suggestions = ref([]);
const showSuggestions = ref(false);

// Определяем, является ли устройство мобильным
const isMobile = ref(false);

onMounted(() => {
  checkIfMobile();
  window.addEventListener('resize', checkIfMobile);
  document.addEventListener('click', closeDropdown);
});

onUnmounted(() => {
  window.removeEventListener('resize', checkIfMobile);
  document.removeEventListener('click', closeDropdown);
});

function checkIfMobile() {
  isMobile.value = window.innerWidth < 768;
}

// Закрыть выпадающий список при клике вне его (для мобильных)
function closeDropdown(event) {
  if (!event.target.closest('.mobile-suggestions-container') &&
      !event.target.closest('input') &&
      !event.target.closest('button')) {
    showSuggestions.value = false;
  }
}

// Вычисляемое свойство для отображения ошибки
const hasError = computed(() => props.error);

// Обновление родительского значения при изменении адреса
watch(address, (newValue) => {
  emit('update:modelValue', newValue);
});

// Обработчик ввода в поле поиска (для мобильных)
function onAddressInput(event) {
  if (event.target.value.trim().length > 3) {
    searchAddress({ query: event.target.value });
    showSuggestions.value = true;
  } else {
    suggestions.value = [];
    showSuggestions.value = false;
  }
}

// Выбор адреса из списка (для мобильных)
function selectAddress(item) {
  if (item) {
    address.value = item.text;
    showSuggestions.value = false;

    // Если у нас есть оригинальный объект с нормализованным адресом
    if (item.original) {
      const originalAddress = item.original;

      // Сохраняем нормализованный результат
      normalizationResult.value = {
        status: 'success',
        message: 'Адрес нормализован',
        is_valid: true,
        normalized_address: originalAddress,
        quality: {
          code: 'GOOD',
          description: 'Адрес полностью нормализован'
        }
      };

      // Уведомляем родительский компонент о нормализованном адресе
      emit('address-normalized', normalizationResult.value);
    }

    // Отправляем обновленное значение в родительский компонент
    emit('update:modelValue', address.value);
  }
}

async function normalizeAddress() {
  if (!address.value) return null;
  normalizing.value = true;
  try {
    // Используем функцию из хранилища
    const response = await cartStore.normalizeAddress(address.value);
    if (response.status === 'success') {
      normalizationResult.value = {
        status: 'success',
        message: response.message || 'Адрес успешно нормализован',
        is_valid: response.is_valid,
        normalized_address: response.normalized_address || {},
        quality: response.quality || {
          code: 'GOOD',
          description: 'Адрес полностью нормализован'
        }
      };
    } else {
      normalizationResult.value = {
        status: 'error',
        message: response.message || 'Не удалось нормализовать адрес',
        is_valid: false,
        normalized_address: {},
        quality: {
          code: '',
          description: ''
        }
      };
    }
    // Уведомляем родительский компонент о результате нормализации
    emit('address-normalized', normalizationResult.value);
    return normalizationResult.value;
  } catch (error) {
    console.error('Ошибка при нормализации адреса:', error);
    const errorResult = {
      status: 'error',
      message: 'Произошла ошибка при нормализации адреса',
      is_valid: false,
      normalized_address: {},
      quality: {
        code: '',
        description: ''
      }
    };
    normalizationResult.value = errorResult;
    emit('address-normalized', errorResult);
    return errorResult;
  } finally {
    normalizing.value = false;
  }
}

// Функция для поиска адресов (автозаполнение)
async function searchAddress(event) {
  if (event.query && event.query.trim().length > 3) {
    loading.value = true;
    try {
      // Сначала попробуем нормализовать введенный адрес
      const response = await axios.post('/api/normalize-address/', {
        address: event.query
      });
      console.log('API Response for suggestions:', response.data);
      if (response.data.status === 'success' && response.data.normalized_address) {
        // Если нормализация успешна, используем нормализованный адрес как подсказку
        const normalizedAddress = response.data.normalized_address;
        // Используем функцию форматирования из хранилища
        const formattedAddress = cartStore.formatAddress(normalizedAddress);
        console.log('Formatted suggestion address:', formattedAddress);
        suggestions.value = [
          {
            text: formattedAddress,
            value: formattedAddress,
            original: normalizedAddress
          }
        ];
      } else {
        // Если нормализация не удалась, предлагаем исходный запрос
        suggestions.value = [{
          text: event.query,
          value: event.query
        }];
      }
    } catch (error) {
      console.error('Ошибка при получении подсказок адресов:', error);
      suggestions.value = [{
        text: event.query,
        value: event.query
      }];
    } finally {
      loading.value = false;
    }
  } else {
    suggestions.value = [];
  }
}

// Обработка выбора адреса из подсказок
function onAddressSelected(event) {
  console.log('Selected item:', event);
  // Если у нас есть оригинальный объект с нормализованным адресом
  if (event.value && event.value.original) {
    // Сохраняем оригинальный объект
    const originalAddress = event.value.original;
    // Форматируем адрес заново из оригинального объекта
    const parts = [];
    if (originalAddress.index) parts.push(originalAddress.index);
    if (originalAddress.region) parts.push(originalAddress.region);
    // Добавляем город только если он отличается от региона
    if (originalAddress.place && originalAddress.place !== originalAddress.region) {
      parts.push(originalAddress.place);
    }
    // Важно! Добавляем микрорайон
    if (originalAddress.location) {
      parts.push(originalAddress.location);
    }
    if (originalAddress.street) parts.push(originalAddress.street);
    if (originalAddress.house) parts.push(originalAddress.house);
    // Форматируем полный адрес
    const formattedAddress = parts.join(', ');
    console.log('Formatted address from original data:', formattedAddress);
    // Устанавливаем отформатированный адрес
    address.value = formattedAddress;
    // Сохраняем нормализованный результат
    normalizationResult.value = {
      status: 'success',
      message: 'Адрес нормализован',
      is_valid: true,
      normalized_address: originalAddress,
      quality: {
        code: 'GOOD',
        description: 'Адрес полностью нормализован'
      }
    };
    // Уведомляем родительский компонент о нормализованном адресе
    emit('address-normalized', normalizationResult.value);
  }
  // Обработка других случаев
  else if (event.value && typeof event.value.value === 'string') {
    address.value = event.value.value;
  } else if (event.value && typeof event.value === 'string') {
    address.value = event.value;
  } else if (event.value && event.value.text) {
    address.value = event.value.text;
  }
  // Отправляем обновленное значение в родительский компонент
  emit('update:modelValue', address.value);
}

// Экспортируем функцию нормализации для использования в родительском компоненте
defineExpose({ normalizeAddress });
</script>

<style scoped>
.address-normalizer {
  margin-bottom: 1rem;
  position: relative;
  width: 100%;
}

/* Стили для результата нормализации */
.normalization-result {
  padding: 0.5rem;
  border-radius: 4px;
  margin-top: 0.5rem;
}

.success-message {
  color: #2c9f2c;
  display: flex;
  align-items: center;
}

.error-message {
  color: #e24c4c;
  display: flex;
  align-items: center;
}

/* Стили для темного поля ввода (сохраняем для всех устройств) */
.dark-input {
  //background-color: #1e1e1e !important;
  color: #fff !important;
  border-color: #333 !important;
}

/* Стили для плейсхолдера в темном поле ввода */
.dark-input::placeholder {
  color: #aaa !important;
}

/* Стили для AutoComplete */
:deep(.p-autocomplete) {
  width: 100%;
}

.position-relative {
  position: relative;
}

.mobile-suggestions-container {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  width: 100%;
  max-height: 200px;
  overflow-y: auto;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 0 0 8px 8px;
  z-index: 9999;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  margin-top: 2px;
}

.suggestion-item {
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  white-space: normal;
  word-break: break-word;
  color: #000; /* Черный цвет текста для подсказок на мобильных */
}

.suggestion-item:hover {
  background-color: #f5f5f5;
}

.cursor-pointer {
  cursor: pointer;
}

.loading-indicator {
  display: flex;
  align-items: center;
  margin-top: 8px;
  font-size: 0.9rem;
  color: #666;
}

/* Стили для компьютера - серый фон и белый текст */
@media (min-width: 768px) {
  :deep(.p-autocomplete-panel) {
    background-color: #1e1e1e !important;
    color: #fff !important;
    border: 1px solid #333 !important;
  }

  :deep(.p-autocomplete-items) {
    background-color: #1e1e1e !important;
  }

  :deep(.p-autocomplete-item) {
    color: #fff !important;
    white-space: normal !important;
    word-break: break-word !important;
    padding: 8px 12px !important;
  }

  :deep(.p-autocomplete-item:hover) {
    background-color: #2a2a2a !important;
  }
}

/* Скрываем/показываем соответствующие виды в зависимости от устройства */
@media (max-width: 767px) {
  .desktop-view {
    display: none;
  }
}

@media (min-width: 768px) {
  .mobile-view {
    display: none;
  }
}

/* Стили для невалидного поля */
:deep(.p-invalid) {
  border-color: #f44336 !important;
}

/* Стили для темного поля ввода */
.dark-input, :deep(.p-inputtext), :deep(.p-autocomplete-input) {
  //background-color: #1e1e1e !important;
  color: #fff !important;
  border-color: #333 !important;
}

/* Стили для плейсхолдера в темном поле ввода */
.dark-input::placeholder, :deep(.p-inputtext::placeholder), :deep(.p-autocomplete-input::placeholder) {
  color: #aaa !important;
}

/* Стили для текста в выбранном элементе */
:deep(.p-autocomplete .p-autocomplete-token-label) {
  color: #fff !important;
}

/* Убедимся, что текст в поле ввода всегда белый */
:deep(.p-autocomplete-input), :deep(.p-autocomplete .p-autocomplete-multiple-container .p-autocomplete-input-token input) {
  color: #fff !important;
}
</style>
