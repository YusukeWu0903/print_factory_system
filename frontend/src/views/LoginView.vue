<script setup>
import { ref } from 'vue'
import { login } from '@/services/auth'
import { dataMode } from '@/services/dataMode'

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
  <main class="min-h-screen flex items-center justify-center bg-stone-100 p-4">
    <form @submit.prevent="handleLogin" class="w-full max-w-sm rounded-2xl bg-white border border-stone-300 shadow-lg p-6 space-y-5">
      <div class="text-center space-y-2">
        <div class="mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-blue-800 flex items-center justify-center text-2xl" aria-hidden="true">印</div>
        <h1 class="text-xl font-bold text-stone-900">印刷廠工單與對帳</h1>
        <p class="text-sm text-gray-600">請以管理員密碼登入</p>
        <p :class="dataMode === 'sandbox' ? 'bg-sky-100 text-sky-900' : 'bg-amber-100 text-stone-900'" class="rounded-lg px-3 py-2 text-sm font-semibold">{{ dataMode === 'sandbox' ? '測試環境' : '正式環境' }}</p>
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
      <button type="submit" :disabled="submitting || !password" class="w-full touch-target rounded-xl bg-blue-700 text-white font-semibold disabled:opacity-50">
        {{ submitting ? '登入中…' : '登入' }}
      </button>
    </form>
  </main>
</template>
