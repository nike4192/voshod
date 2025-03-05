<template>
  <div>
    <div class="flex justify-content-between flex-wrap">
      <h1 class="text-7xl" style="margin-block-start:0px">Voshod</h1>
      <Button @click="basket" style="width:50px; height:50px;" icon="pi pi-shopping-cart"></Button>
    </div>
    <div class="flex justify-content-center flex-wrap">
      <h1 style="margin-block-start:0px">Товары</h1>
    </div>
<!--style="margin-left:5rem;margin-right:5rem"-->
    <div class="grid m-8"   >
      <div v-for="product in products" :key="product.id" class="col-4 " >
        <Card class="w-full" style="overflow: hidden">
          <template #header>
            <img :src="product.image" class="w-full"/>
          </template>
          <template #title>{{ product.name }}</template>
          <template #subtitle>{{ product.price }} &#8381</template>
          <template #content>
            <p class="m-0">

            </p>
          </template>
          <template #footer>
            <div class="flex gap-4 mt-1">
              <Button label="В корзину" class="w-full" @click="cartStore.addCart(product.id)"/>
            </div>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>


<script setup>

import {useProducts} from '~/composables/useProduct.js';
import {useCart} from '~/composables/useCart.js';

import {ref, onMounted} from 'vue';

const products = ref([]);
const error = ref(null);

const router = useRouter();

const cartStore =  useCart()


const basket = () => {
  router.push('/cart');
};

onMounted(async () => {
  const productStore = await useProducts();
  await cartStore.fetchCart()
  products.value = productStore.products;
  error.value = productStore.error;

})

</script>

<style>
.my-gutter [class*=col-4] {
  padding: 2rem;

}

</style>
