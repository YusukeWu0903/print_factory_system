<script setup>
import { onMounted, reactive, ref } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { useClients } from '@/composables/useApi'

const { clients, loading, error, fetchClients, createClient, updateClient, deleteClient } = useClients()
const formOpen = ref(false)
const editingId = ref(null)
const saving = ref(false)
const deletingId = ref(null)
const formError = ref('')
const form = reactive({ name: '', tax_id: '', billing_cycle: 15 })

const resetForm = () => {
  formOpen.value = false
  editingId.value = null
  form.name = ''
  form.tax_id = ''
  form.billing_cycle = 15
  formError.value = ''
}

const editClient = (client) => {
  formOpen.value = true
  editingId.value = client.id
  form.name = client.name
  form.tax_id = client.tax_id || ''
  form.billing_cycle = client.billing_cycle
  formError.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const saveClient = async () => {
  formError.value = ''
  if (!form.name.trim()) {
    formError.value = '請輸入客戶名稱'
    return
  }
  if (form.tax_id && !/^[0-9]{8}$/.test(form.tax_id)) {
    formError.value = '統一編號須為 8 碼數字'
    return
  }
  if (!Number.isInteger(form.billing_cycle) || form.billing_cycle < 1 || form.billing_cycle > 31) {
    formError.value = '結帳日須介於 1 至 31 號'
    return
  }

  saving.value = true
  const payload = {
    name: form.name.trim(),
    tax_id: form.tax_id || null,
    billing_cycle: form.billing_cycle,
  }
  try {
    if (editingId.value) await updateClient(editingId.value, payload)
    else await createClient(payload)
    resetForm()
    await fetchClients()
  } catch (err) {
    formError.value = err.response?.data?.detail || '儲存客戶失敗'
  } finally {
    saving.value = false
  }
}

const removeClient = async (client) => {
  if (!confirm(`確定刪除「${client.name}」？若已有工單，系統會拒絕刪除。`)) return
  deletingId.value = client.id
  formError.value = ''
  try {
    await deleteClient(client.id)
    if (editingId.value === client.id) resetForm()
  } catch (err) {
    formError.value = err.response?.data?.detail || '刪除客戶失敗'
  } finally {
    deletingId.value = null
  }
}

onMounted(fetchClients)
</script>

<template>
  <AppLayout title="客戶管理">
    <div class="p-3 space-y-4 max-w-3xl mx-auto">
      <button v-if="!formOpen" class="touch-target rounded-lg bg-blue-700 text-white px-5" @click="formOpen = true">新增客戶</button>
      <p v-if="!formOpen && formError" role="alert" class="text-red-700">{{ formError }}</p>
      <form v-if="formOpen" @submit.prevent="saveClient" class="bg-white rounded-xl border border-stone-300 shadow-sm p-4 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-stone-900">{{ editingId ? '編輯客戶' : '新增客戶' }}</h2>
          <button type="button" @click="resetForm" class="text-sm text-blue-800 underline">取消</button>
        </div>
        <div>
          <label for="client-name" class="block text-sm font-medium text-gray-700 mb-1">客戶名稱 *</label>
          <input id="client-name" v-model="form.name" type="text" maxlength="100" autocomplete="organization" required class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2" />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label for="client-tax-id" class="block text-sm font-medium text-gray-700 mb-1">統一編號（選填）</label>
            <input id="client-tax-id" v-model="form.tax_id" type="text" inputmode="numeric" maxlength="8" placeholder="8 碼數字" class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2" />
          </div>
          <div>
            <label for="client-billing-cycle" class="block text-sm font-medium text-gray-700 mb-1">每月結帳日</label>
            <select id="client-billing-cycle" v-model.number="form.billing_cycle" class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2 bg-white">
              <option v-for="day in 31" :key="day" :value="day">{{ day }} 號</option>
            </select>
          </div>
        </div>
        <p class="text-xs text-gray-500">對帳月份以此日截止；短月的 31 號改以月底截止。</p>
        <p v-if="formError" role="alert" class="text-sm text-red-700 bg-red-50 rounded-lg p-3">{{ formError }}</p>
        <button type="submit" :disabled="saving" class="w-full touch-target rounded-xl bg-blue-700 text-white font-semibold disabled:opacity-50">
          {{ saving ? '儲存中…' : editingId ? '儲存修改' : '新增客戶' }}
        </button>
      </form>

      <section class="bg-white rounded-xl border border-stone-300 shadow-sm p-4">
        <h2 class="font-semibold text-stone-900 mb-3">客戶列表</h2>
        <p v-if="loading" class="text-sm text-gray-500">載入中…</p>
        <p v-else-if="error" role="alert" class="text-sm text-red-700">{{ error }} <button type="button" @click="fetchClients" class="underline">重試</button></p>
        <p v-else-if="clients.length === 0" class="text-sm text-gray-500">尚無客戶</p>
        <div v-else class="divide-y divide-gray-100">
          <article v-for="client in clients" :key="client.id" class="py-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 class="font-medium text-gray-800">{{ client.name }}</h3>
              <p class="text-xs text-gray-500">統編：{{ client.tax_id || '未填' }} · 每月 {{ client.billing_cycle }} 號結帳</p>
            </div>
            <div class="flex gap-2">
              <button type="button" @click="editClient(client)" class="touch-target px-3 rounded-lg bg-stone-100 text-amber-800">編輯</button>
              <button type="button" @click="removeClient(client)" :disabled="deletingId === client.id" class="touch-target px-3 rounded-lg bg-red-50 text-red-700 disabled:opacity-50">刪除</button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </AppLayout>
</template>
