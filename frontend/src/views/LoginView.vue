<script setup>
import { ref } from 'vue'
import { login } from '@/services/auth'

const password = ref('')
const error = ref('')
const submitting = ref(false)

const handleLogin = async () => {
  if (!password.value || submitting.value) return
  error.value = ''
  submitting.value = true
  try {
    await login(password.value)
    password.value = ''
  } catch (err) {
    error.value = err.message || '登入失敗'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="min-h-screen flex items-center justify-center bg-gradient-to-b from-amber-50 via-orange-50 to-amber-100 p-4">
    <form @submit.prevent="handleLogin" class="w-full max-w-sm rounded-2xl bg-white border border-amber-100 shadow-lg p-6 space-y-5">
      <div class="text-center space-y-2">
        <div class="mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center text-2xl" aria-hidden="true">🏭</div>
        <h1 class="text-xl font-bold text-amber-900">印刷廠工單與對帳</h1>
        <p class="text-sm text-gray-600">請以管理員密碼登入</p>
      </div>
      <div>
        <label for="admin-password" class="block text-sm font-medium text-gray-700 mb-1.5">管理員密碼</label>
        <input
          id="admin-password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
          class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-amber-500"
        />
      </div>
      <p v-if="error" role="alert" class="text-sm text-red-700 bg-red-50 rounded-lg p-3">{{ error }}</p>
      <button type="submit" :disabled="submitting || !password" class="w-full touch-target rounded-xl bg-amber-600 text-white font-semibold disabled:opacity-50">
        {{ submitting ? '登入中…' : '登入' }}
      </button>
    </form>
  </main>
</template>
