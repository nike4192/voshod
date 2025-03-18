<template>
  <div class="address-normalizer">
    <div class="p-field">
      <label for="address">Адрес доставки</label>
      <AutoComplete
          id="address"
          v-model="address"
          class="w-full"
          placeholder="Введите адрес доставки"
          :suggestions="suggestions"
          @complete="searchAddress"
          @item-select="onAddressSelected"
          :dropdown="true"
          :class="{ 'p-invalid': hasError }"
          optionLabel="text"
          :loading="loading"
          :delay="500"
          :minLength="3"
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

// Функция для поиска адресов (автозаполнение)
async function searchAddress(event) {
  if (event.query.trim().length > 3) {
    loading.value = true;
    try {
      // Отправляем запрос для получения вариантов адресов
      const response = await axios.post('/api/address-suggestions/', {
        query: event.query
      });

      console.log('API Response for suggestions:', response.data);

      // Проверяем успешность ответа и наличие массива подсказок
      if (response.data.status === 'success' && Array.isArray(response.data.suggestions)) {
        // Используем подсказки из ответа API
        suggestions.value = response.data.suggestions;

        // Если подсказок нет, добавляем введенный текст как подсказку
        if (suggestions.value.length === 0) {
          suggestions.value = [{
            text: event.query,
            value: event.query
          }];
        }
      } else {
        // Если API не вернуло подсказки, создаем одну подсказку из введенного текста
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

  // Проверяем, что у нас есть выбранный элемент
  if (!event || !event.value) {
    console.error('No selected item or value');
    return;
  }

  // Обновляем значение адреса
  if (typeof event.value === 'object') {
    // Если event.value - это объект
    if (event.value.value) {
      address.value = event.value.value;
    } else if (event.value.text) {
      address.value = event.value.text;
    }

    // Если у нас есть оригинальный объект с нормализованным адресом, сохраняем его
    if (event.value.original) {
      normalizationResult.value = {
        status: 'success',
        message: 'Адрес нормализован',
        is_valid: true,
        normalized_address: event.value.original,
        quality: {
          code: 'GOOD', // Предполагаем, что качество хорошее, так как это результат нормализации
          description: 'Адрес полностью нормализован'
        }
      };

      // Уведомляем родительский компонент о нормализованном адресе
      emit('address-normalized', normalizationResult.value);
    }
  } else if (typeof event.value === 'string') {
    // Если event.value - это строка
    address.value = event.value;
  }

  // Отправляем обновленное значение в родительский компонент
  emit('update:modelValue', address.value);

  // Очищаем подсказки
  suggestions.value = [];
}
// Функция нормализации адреса (будет вызываться из родительского компонента)
async function normalizeAddress() {
  if (!address.value) return null;

  // Если у нас уже есть нормализованный результат, возвращаем его
  if (normalizationResult.value &&
      normalizationResult.value.status === 'success' &&
      normalizationResult.value.normalized_address) {
    return normalizationResult.value;
  }

  normalizing.value = true;
  try {
    const response = await axios.post('/api/normalize-address/', {
      address: address.value
    });

    console.log('Normalized address response:', response.data);

    if (response.data.status === 'success') {
      normalizationResult.value = {
        status: 'success',
        message: response.data.message || 'Адрес успешно нормализован',
        is_valid: true,
        normalized_address: response.data.normalized_address || {},
        quality: {
          code: response.data.quality_code || 'GOOD',
          description: response.data.quality_description || 'Адрес полностью нормализован'
        }
      };
    } else {
      normalizationResult.value = {
        status: 'error',
        message: response.data.message || 'Не удалось нормализовать адрес',
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