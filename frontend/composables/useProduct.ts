import { Ref, ref } from 'vue';
import { useAsyncData } from '#app'; // Или 'nuxt/app' в зависимости от версии Nuxt

export interface Product {
  id: number;
  name: string;
  price: number;
}

export async function useProducts() {
  const products = await $fetch<Product[]>('/api/product/', {baseURL: 'http://localhost'});
  const error = null;

  console.log(products, error,);

  return {
    products,
    error,
  };
}
