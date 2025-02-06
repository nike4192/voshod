import { Ref, ref } from 'vue';
import { useAsyncData } from '#app'; // Или 'nuxt/app' в зависимости от версии Nuxt

export interface Product {
  id: number;
  name: string;
  price: number;
}

export function useProducts() {
  const products: Ref<Product[]> = ref([]);
  const error: Ref<any> = ref(null);

  const fetchProducts = async () => {
    try {
      const { data } = await useFetch<Product[]>('/api/products/');
      products.value = data.value || [];
    } catch (err) {
      error.value = err;
      console.error('Ошибка при загрузке товаров:', err);
    }
  };

  return {
    products,
    error,
    fetchProducts,
  };
}