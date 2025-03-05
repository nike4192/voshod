// https://nuxt.com/docs/api/configuration/nuxt-config
import {NuxtConfig} from '@nuxt/types';
import Aura from '@primevue/themes/aura';


export default defineNuxtConfig({
    compatibilityDate: '2025-02-21',


    // // devtools: { enabled: true },
    // nitro: {
    //     preset: 'node-server', // или другой подходящий пресет
    // },

    // server: {
    //     host: '0.0.0.0', // Должно быть строкой
    //     port: 3000,
    // },
    css: [
        'primevue/resources/themes/aura-dark-noir/theme.css', // Тема
        'primevue/resources/primevue.min.css', // Основные стили PrimeVue
        'primeicons/primeicons.css', // Иконки
        'primeflex/primeflex.css', // Утилиты для верстки
    ],

    // vite: {
    //     server: {
    //         hmr: {
    //             protocol: 'ws',
    //             host: 'localhost',
    //             port: 80
    //         }
    //     }
    // },





     modules: ['@primevue/nuxt-module', '@pinia/nuxt'],
     primevue: {
         options: {
             theme: {
                 preset: Aura,
             },
         }
     },

});