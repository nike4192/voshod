<template>
  <div class="p-fluid">
    <!-- Стандартный AutoComplete для компьютеров -->
    <div class="desktop-view" v-if="!isMobile">
      <AutoComplete
        v-model="selectedCity"
        :suggestions="suggestions"
        :class="{ 'p-invalid': hasError }"
        class="w-full"
        optionLabel="fullName"
        :dropdown="true"
        :forceSelection="true"
        @complete="searchCities"
        @item-select="handleCitySelect"
        @clear="handleCityClear"
        placeholder="Введите название города (минимум 3 символа)"
        :loading="loading"
        appendTo="body"
      >
        <template #empty>
          <div class="p-2">Города не найдены</div>
        </template>
        <template #loader>
          <div class="p-2">Поиск городов...</div>
        </template>
        <template #item="slotProps">
          <div>{{ slotProps.item.fullName }}</div>
        </template>
        <template #selectedItem="slotProps">
          <div>{{ slotProps.item.fullName }}</div>
        </template>
      </AutoComplete>
    </div>

    <!-- Кастомная реализация для мобильных устройств -->
    <div class="mobile-view" v-else>
      <!-- Поле ввода для поиска -->
      <div class="p-inputgroup">
        <InputText
          v-model="searchQuery"
          placeholder="Введите название города"
          :class="{ 'p-invalid': hasError }"
          @input="onSearchInput"
          class="dark-input"
        />
        <Button icon="pi pi-search" @click="showSuggestions = true" />
      </div>

      <!-- Выпадающий список с результатами -->
      <div v-if="showSuggestions && suggestions.length > 0" class="suggestions-container">
        <div
          v-for="item in suggestions"
          :key="item.code"
          class="suggestion-item p-2 cursor-pointer"
          @click="selectCity(item)"
        >
          {{ item.fullName }}
        </div>
      </div>
    </div>

    <small v-if="hasError" class="p-error">Выберите город из списка</small>

    <!-- Индикатор загрузки для мобильных -->
    <div v-if="loading && isMobile" class="loading-indicator">
      <ProgressSpinner style="width:30px;height:30px" />
      <span class="ml-2">Поиск...</span>
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

const emit = defineEmits(['update:modelValue', 'city-selected']);

const searchQuery = ref('');
const loading = ref(false);
const suggestions = ref([]);
const selectedCity = ref(null);
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

// Вычисляемое свойство для отображения ошибки
const hasError = computed(() => props.error);

// Обновление родительского значения при изменении города
watch(selectedCity, (newValue) => {
  if (newValue) {
    emit('update:modelValue', typeof newValue === 'object' ? newValue.fullName : newValue);
  } else {
    emit('update:modelValue', '');
  }
});

// Обработчик ввода в поле поиска (для мобильных)
function onSearchInput(event) {
  if (event.target.value.trim().length >= 3) {
    searchCities({ query: event.target.value });
    showSuggestions.value = true;
  } else {
    suggestions.value = [];
    showSuggestions.value = false;
  }
}

// Функция для поиска городов CDEK
async function searchCities(event) {
  if (event.query && event.query.trim().length < 3) {
    suggestions.value = [];
    return;
  }

  const query = event.query || searchQuery.value;

  if (query.trim().length < 3) {
    suggestions.value = [];
    return;
  }

  loading.value = true;
  try {
    const response = await axios.get('/api/suggest-cities/', {
      params: {
        query: query
      }
    });

    if (response.data && response.data.status === 'success' && Array.isArray(response.data.cities)) {
      suggestions.value = response.data.cities.map(city => {
        return {
          cityUuid: city.city_uuid,
          code: city.code,
          fullName: city.full_name
        };
      });
    } else {
      suggestions.value = [];
    }
  } catch (error) {
    console.error('Ошибка при поиске городов CDEK:', error);
    suggestions.value = [];
  } finally {
    loading.value = false;
  }
}

// Обработчик выбора города (для стандартного AutoComplete)
function handleCitySelect(event) {
  if (event && event.value) {
    selectedCity.value = event.value;
    emit('city-selected', {
      code: event.value.code,
      fullName: event.value.fullName,
      cityUuid: event.value.cityUuid || ''
    });
  }
}

// Выбор города из списка (для мобильных)
function selectCity(city) {
  selectedCity.value = city;
  searchQuery.value = city.fullName;
  showSuggestions.value = false;

  emit('city-selected', {
    code: city.code,
    fullName: city.fullName,
    cityUuid: city.cityUuid || ''
  });
}

// Обработчик очистки поля
function handleCityClear() {
  selectedCity.value = null;
  emit('city-selected', null);
}

// Закрыть выпадающий список при клике вне его (для мобильных)
function closeDropdown(event) {
  if (!event.target.closest('.suggestions-container') &&
      !event.target.closest('input') &&
      !event.target.closest('button')) {
    showSuggestions.value = false;
  }
}
</script>

<style scoped>
/* Стили для мобильного выпадающего списка */
.suggestions-container {
  position: absolute;
  width: calc(100% - 20px);
  max-height: 200px;
  overflow-y: auto;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  z-index: 1000;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  margin-top: 5px;
  left: 10px;
  right: 10px;
}

.suggestion-item {
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  white-space: normal;
  word-break: break-word;
  color: #000; /* Черный цвет текста для подсказок */
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

/* Стили для темного поля ввода */
.dark-input {
  //background-color: #1e1e1e !important;
  color: #fff !important;
  border-color: #333 !important;
}

/* Стили для плейсхолдера в темном поле ввода */
.dark-input::placeholder {
  color: #aaa !important;
}

/* Стили для AutoComplete на десктопе */
:deep(.p-autocomplete-panel) {
  background-color: #fff !important;
  color: #000 !important;
  border: 1px solid #ddd !important;
  max-height: 300px !important;
  overflow-y: auto !important;
  z-index: 1000 !important;
}

:deep(.p-autocomplete-items) {
  padding: 0 !important;
}

:deep(.p-autocomplete-item) {
  padding: 8px 12px !important;
  color: #000 !important;
  border-bottom: 1px solid #eee !important;
  white-space: normal !important;
  word-break: break-word !important;
}

:deep(.p-autocomplete-item:hover) {
  background-color: #f5f5f5 !important;
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
</style>