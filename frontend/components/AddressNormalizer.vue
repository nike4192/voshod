<template>
  <div class="address-normalizer">
    <div class="p-field">
      <label for="address">Адрес доставки</label>
      <AutoComplete
        id="address"
        v-model="address"
        class="w-full"
        placeholder="Введите адрес доставки: Город, Улица, Дом"
        :suggestions="suggestions"
        @complete="searchAddress"
        @item-select="onAddressSelected"
        :dropdown="true"
        :class="{ 'p-invalid': hasError }"
        optionLabel="text"
        :loading="loading"
      />
      <small v-if="hasError" class="p-error">
        Пожалуйста, введите адрес доставки
      </small>
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
import { ref, defineEmits, defineProps, watch, computed } from 'vue';
import AutoComplete from 'primevue/autocomplete';
import axios from 'axios';
const cartStore = useCart();
import { useCart } from '~/composables/useCart.js';
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

// Вычисляемое свойство для отображения ошибки
const hasError = computed(() => props.error);

// Обновление родительского значения при изменении адреса
watch(address, (newValue) => {
  emit('update:modelValue', newValue);
});
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
  if (event.query.trim().length > 3) {
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

/* Дополнительные стили для автозаполнения */
:deep(.p-autocomplete) {
  width: 100%;
}

:deep(.p-autocomplete-panel) {
  max-width: 100%;
  z-index: 1000;
}

:deep(.p-autocomplete-items) {
  padding: 0.5rem 0;
}

:deep(.p-autocomplete-item) {
  padding: 0.5rem 1rem;
  cursor: pointer;
  white-space: normal;
  word-break: break-word;
}

:deep(.p-autocomplete-item:hover) {
  background-color: #f5f5f5;
}
</style>