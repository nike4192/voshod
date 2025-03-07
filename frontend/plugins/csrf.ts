// plugins/csrf.ts
import { useCookie, defineNuxtPlugin } from '#app'

export default defineNuxtPlugin((nuxtApp) => {
  // Функция для получения нового CSRF-токена
  const refreshCsrfToken = async () => {
    try {
      // Используем нативный fetch для получения нового токена
      await fetch('/api/get-csrf-token/', {
        method: 'GET',
        credentials: 'include' // Важно для сохранения cookies
      })

      // Возвращаем новый токен из cookies
      return useCookie('csrftoken').value
    } catch (error) {
      console.error('Failed to refresh CSRF token:', error)
      return null
    }
  }

  // Сохраняем оригинальную функцию $fetch
  const originalFetch = globalThis.$fetch || globalThis.fetch

  // Создаем собственный перехватчик для $fetch
  globalThis.$fetch = async (request, options = {}) => {
    // Получаем текущий CSRF-токен из cookies
    let csrfToken = useCookie('csrftoken').value

    // Если токена нет, пробуем получить новый
    if (!csrfToken) {
      csrfToken = await refreshCsrfToken()
    }

    // Настраиваем заголовки для запроса
    const headers = {
      ...(options.headers || {}),
    }

    // Добавляем CSRF-токен в заголовки, если он есть
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken
    }

    // Обновляем опции запроса
    const updatedOptions = {
      ...options,
      headers,
      credentials: 'include', // Важно для работы с cookies
    }

    try {
      // Выполняем запрос с CSRF-токеном
      return await originalFetch(request, updatedOptions)
    } catch (error) {
      // Если получили 403, возможно, CSRF-токен устарел
      if (error.response?.status === 403) {
        // Пробуем получить новый токен
        const newToken = await refreshCsrfToken()

        if (newToken) {
          // Обновляем заголовок с новым токеном
          updatedOptions.headers = {
            ...updatedOptions.headers,
            'X-CSRFToken': newToken
          }

          // Повторяем запрос с новым токеном
          return await originalFetch(request, updatedOptions)
        }
      }

      // Если не удалось решить проблему, пробрасываем ошибку дальше
      throw error
    }
  }

  // Альтернативный подход - создание собственного провайдера для useFetch
  nuxtApp.provide('csrf', {
    getToken: () => useCookie('csrftoken').value,
    refreshToken: refreshCsrfToken,
    fetch: async (url, options = {}) => {
      let csrfToken = useCookie('csrftoken').value

      if (!csrfToken) {
        csrfToken = await refreshCsrfToken()
      }

      return $fetch(url, {
        ...options,
        headers: {
          ...(options.headers || {}),
          'X-CSRFToken': csrfToken
        },
        credentials: 'include'
      })
    }
  })

  // Добавляем промежуточное ПО для перехвата useFetch
  nuxtApp.hook('app:created', () => {
    // Перехватываем все вызовы useFetch для добавления CSRF-токена
    const originalUseFetch = nuxtApp.$fetch

    if (originalUseFetch) {
      nuxtApp.$fetch = (request, options = {}) => {
        const csrfToken = useCookie('csrftoken').value

        if (csrfToken) {
          options.headers = {
            ...(options.headers || {}),
            'X-CSRFToken': csrfToken
          }
        }

        options.credentials = 'include'
        return originalUseFetch(request, options)
      }
    }
  })
})