<script setup>
import {onMounted} from "vue";
import {useCart} from "~/composables/useCart.js";

const router = useRouter();
const cartStore = useCart()
onMounted(async () => {

  await cartStore.fetchCart()

})

</script>

<template>
<!--  <div>-->
<!--    <button -->
<!--  </div>-->
  <h1>1</h1>
  <template v-if="cartStore.cartRef">
  <div v-for="(value, key) in cartStore.cartRef">
    <li>
      {{key}}
    </li>
  </div>
  </template>
</template>

<style scoped>

</style>