<template>
  <div class="address-normalizer">
    <div class="p-field">
      <label for="address">Адрес доставки</label>
      <div class="p-inputgroup">
        <InputText
          id="address"
          v-model="address"
          class="w-full"
          placeholder="Введите адрес доставки"
          :class="{ 'p-invalid': v$.delivery_address.$invalid && v$.delivery_address.$dirty }"
        />
        <Button
          icon="pi pi-check"
          @click="normalizeUserAddress"
          :loading="normalizing"
          :disabled="!address"
        />
      </div>
      <small v-if="v$.delivery_address.$invalid && v$.delivery_address.$dirty" class="p-error">
        {{ v$.delivery_address.$errors[0].$message }}
      </small>
    </div>

    <div v-if="normalizationResult" class="mt-3">
      <div v-if="normalizationResult.status === 'success'" class="p-card p-3">
        <div class="address-result">
          <h4>Нормализованный адрес:</h4>
          <p class="normalized-address">{{ normalizationResult.normalized_address }}</p>

          <div class="quality-info" :class="{
            'quality-good': normalizationResult.is_valid,
            'quality-bad': !normalizationResult.is_valid
          }">
            <i :class="normalizationResult.is_valid ? 'pi pi-check-circle' : 'pi pi-exclamation-triangle'"></i>
            <span>{{ normalizationResult.quality.description }}</span>
          </div>

          <div v-if="normalizationResult.postal_code" class="postal-code">
            <strong>Почтовый индекс:</strong> {{ normalizationResult.postal_code }}
          </div>

          <Button
            v-if="normalizationResult.is_valid"
            label="Использовать этот адрес"
            class="p-button-success mt-3"
            @click="useNormalizedAddress"
          />
        </div>
      </div>
      <div v-else class="p-card p-3 error-result">
        <i class="pi pi-times-circle"></i>
        <p>{{ normalizationResult.message }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useVuelidate } from '@vuelidate/core';
import { required } from '@vuelidate/validators';
import { useCart } from '~/composables/useCart.js';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  validationRules: {
    type: Object,
    default: () => ({ required })
  }
});

const emit = defineEmits(['update:modelValue', 'address-normalized']);

const cartStore = useCart();
const address = ref(props.modelValue);
const normalizing = ref(false);
const normalizationResult = ref(null);

// Валидация
const rules = {
  delivery_address: props.validationRules
};

const v$ = useVuelidate(rules, {
  delivery_address: address
});

// Следим за изменениями входного значения
watch(() => props.modelValue, (newValue) => {
  address.value = newValue;
});

// Следим за изменениями локального значения
watch(address, (newValue) => {
  emit('update:modelValue', newValue);
});

async function normalizeUserAddress() {
  if (!address.value) return;

  normalizing.value = true;
  try {
    normalizationResult.value = await cartStore.normalizeAddress(address.value);

    // Если нормализация успешна, уведомляем родительский компонент
    if (normalizationResult.value.status === 'success') {
      emit('address-normalized', normalizationResult.value);
    }
  } catch (error) {
    console.error('Ошибка при нормализации адреса:', error);
  } finally {
    normalizing.value = false;
  }
}

function useNormalizedAddress() {
  if (normalizationResult.value && normalizationResult.value.status === 'success') {
    address.value = normalizationResult.value.normalized_address;
    emit('update:modelValue', address.value);
  }
}
</script>

<style scoped>
.address-normalizer {
  max-width: 100%;
}

.normalized-address {
  font-weight: 500;
  margin: 10px 0;
}

.quality-info {
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 4px;
  margin: 10px 0;
}

.quality-info i {
  margin-right: 8px;
}

.quality-good {
  background-color: #e6f7e6;
  color: #2c8c2c;
}

.quality-bad {
  background-color: #fff2e6;
  color: #cc7700;
}

.postal-code {
  margin-top: 10px;
}

.error-result {
  color: #cc0000;
  display: flex;
  align-items: center;
}

.error-result i {
  margin-right: 8px;
  font-size: 1.5rem;
}
</style>