<template>
  <div class="p-fluid">
    <!-- Стандартный Dropdown для компьютеров -->
    <div class="desktop-view" v-if="!isMobile">
      <Dropdown
        v-model="selectedPickupPoint"
        :options="pickupPoints"
        :class="{ 'p-invalid': hasError }"
        class="w-full"
        optionLabel="fullDescription"
        placeholder="Выберите пункт выдачи"
        :loading="loading"
        :disabled="!props.cityCode || pickupPoints.length === 0"
        @change="handlePickupPointSelect"
        appendTo="body"
      >
        <template #empty>
          <div class="p-2">Пункты выдачи не найдены</div>
        </template>
        <template #option="slotProps">
          <div>
            <div><strong>{{ slotProps.option.name }}</strong></div>
            <div>{{ slotProps.option.address }}</div>
            <div v-if="slotProps.option.workTime"><small>Режим работы: {{ slotProps.option.workTime }}</small></div>
            <div v-if="slotProps.option.phone"><small>Телефон: {{ slotProps.option.phone }}</small></div>
          </div>
        </template>
        <template #value="slotProps">
          <div v-if="slotProps.value">
            <div><strong>{{ slotProps.value.name }}</strong></div>
            <div>{{ slotProps.value.address }}</div>
          </div>
          <div v-else>Выберите пункт выдачи</div>
        </template>
      </Dropdown>
    </div>

    <!-- Кастомная реализация для мобильных устройств -->
    <div class="mobile-view" v-else>
      <!-- Поле ввода, которое открывает диалог -->
      <div class="p-inputgroup">
        <InputText
          v-model="displayValue"
          readonly
          placeholder="Выберите пункт выдачи"
          @click="openDialog"
          :class="{ 'p-invalid': hasError }"
          :disabled="!props.cityCode || pickupPoints.length === 0"
          class="dark-input"
        />
        <Button
          icon="pi pi-map-marker"
          @click="openDialog"
          :disabled="!props.cityCode || pickupPoints.length === 0"
        />
      </div>

      <!-- Диалог для выбора пункта выдачи -->
      <Dialog
        v-model:visible="dialogVisible"
        header="Выберите пункт выдачи"
        :style="{width: '90vw', maxWidth: '500px'}"
        :modal="true"
      >
        <div v-if="loading" class="p-d-flex p-jc-center p-ai-center p-my-3">
          <ProgressSpinner style="width:50px;height:50px" />
          <span class="ml-2">Загрузка пунктов выдачи...</span>
        </div>

        <div v-else-if="pickupPoints.length === 0" class="p-text-center p-my-3">
          Пункты выдачи не найдены
        </div>

        <div v-else class="pickup-point-list" style="max-height: 60vh; overflow-y: auto;">
          <div
            v-for="point in pickupPoints"
            :key="point.code"
            class="pickup-point-item p-3 border-bottom-1 surface-border cursor-pointer"
            @click="selectPickupPoint(point)"
          >
            <div><strong>{{ point.name }}</strong></div>
            <div>{{ point.address }}</div>
            <div v-if="point.workTime"><small>Режим работы: {{ point.workTime }}</small></div>
            <div v-if="point.phone"><small>Телефон: {{ point.phone }}</small></div>
          </div>
        </div>
      </Dialog>
    </div>

    <small v-if="hasError" class="p-error">Выберите пункт выдачи</small>
    <small v-if="props.cityCode && pickupPoints.length === 0 && !loading" class="p-info">
      В выбранном городе нет доступных пунктов выдачи СДЭК
    </small>
  </div>
</template>

<script setup>
import { ref, defineEmits, defineProps, watch, computed, onMounted, onUnmounted } from 'vue';
import Dropdown from 'primevue/dropdown';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import ProgressSpinner from 'primevue/progressspinner';
import axios from 'axios';
import { useCart } from '~/composables/useCart.js';

const cartStore = useCart();

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  cityCode: {
    type: String,
    default: ''
  },
  error: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue', 'pickup-point-selected']);

const displayValue = ref(props.modelValue || '');
const loading = ref(false);
const pickupPoints = ref([]);
const selectedPickupPoint = ref(null);
const dialogVisible = ref(false);

// Определяем, является ли устройство мобильным
const isMobile = ref(false);

onMounted(() => {
  checkIfMobile();
  window.addEventListener('resize', checkIfMobile);
});

onUnmounted(() => {
  window.removeEventListener('resize', checkIfMobile);
});

function checkIfMobile() {
  isMobile.value = window.innerWidth < 768;
}

// Вычисляемое свойство для отображения ошибки
const hasError = computed(() => props.error);

// Обновление родительского значения при изменении пункта выдачи
watch(displayValue, (newValue) => {
  emit('update:modelValue', newValue);
});

// Загрузка пунктов выдачи при изменении кода города
watch(() => props.cityCode, async (newCityCode) => {
  if (newCityCode) {
    await fetchPickupPoints(newCityCode);
  } else {
    pickupPoints.value = [];
    selectedPickupPoint.value = null;
    displayValue.value = '';
  }
}, { immediate: true });

// Открыть диалог для мобильных
function openDialog() {
  if (!props.cityCode || pickupPoints.value.length === 0) return;
  dialogVisible.value = true;
}

// Функция для загрузки пунктов выдачи CDEK по коду города
async function fetchPickupPoints(cityCode) {
  if (!cityCode) return;

  loading.value = true;
  pickupPoints.value = [];
  selectedPickupPoint.value = null;
  displayValue.value = '';

  try {
    const response = await axios.get('/api/cdek-delivery-points/', {
      params: {
        city_code: cityCode
      }
    });

    if (response.data.status === 'success' && Array.isArray(response.data.delivery_points)) {
      pickupPoints.value = response.data.delivery_points.map(point => ({
        code: point.code,
        name: point.name,
        address: point.address,
        workTime: point.work_time,
        phone: point.phone,
        fullDescription: `${point.name} (${point.address})`
      }));
    } else {
      console.warn('No delivery points found or unexpected API response format:', response.data);
    }
  } catch (error) {
    console.error('Ошибка при загрузке пунктов выдачи CDEK:', error);
  } finally {
    loading.value = false;
  }
}

// Обработчик выбора пункта выдачи (для стандартного Dropdown)
function handlePickupPointSelect(event) {
  if (event && event.value) {
    selectedPickupPoint.value = event.value;
    displayValue.value = event.value.address;

    emit('pickup-point-selected', {
      code: event.value.code,
      address: event.value.address,
      name: event.value.name || '',
      workTime: event.value.workTime || '',
      phone: event.value.phone || ''
    });
  }
}

// Выбор пункта выдачи из диалога (для мобильных)
function selectPickupPoint(point) {
  selectedPickupPoint.value = point;
  displayValue.value = point.address;
  dialogVisible.value = false;

  emit('pickup-point-selected', {
    code: point.code,
    address: point.address,
    name: point.name || '',
    workTime: point.workTime || '',
    phone: point.phone || ''
  });
}
</script>

<style scoped>
/* Стили для мобильного диалога */
.pickup-point-item {
  transition: background-color 0.2s;
}

.pickup-point-item:hover {
  background-color: var(--surface-hover);
}

.cursor-pointer {
  cursor: pointer;
}

/* Стили для темного поля ввода */
.dark-input {
  background-color: #1e1e1e !important;
  color: #fff !important;
  border-color: #333 !important;
}

/* Стили для плейсхолдера в темном поле ввода */
.dark-input::placeholder {
  color: #aaa !important;
}

/* Стили для Dropdown на десктопе */
:deep(.p-dropdown-panel) {
  background-color: #fff !important;
  color: #000 !important;
  border: 1px solid #ddd !important;
  max-height: 300px !important;
  overflow-y: auto !important;
  z-index: 1000 !important;
}

:deep(.p-dropdown-items) {
  padding: 0 !important;
}

:deep(.p-dropdown-item) {
  padding: 8px 12px !important;
  color: #000 !important;
  border-bottom: 1px solid #eee !important;
  white-space: normal !important;
  word-break: break-word !important;
}

:deep(.p-dropdown-item:hover) {
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