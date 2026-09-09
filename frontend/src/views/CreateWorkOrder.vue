<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { useWorkOrders, useClients } from '@/composables/useApi'

const router = useRouter()
const route = useRoute()

const { createWorkOrder, loading: createLoading } = useWorkOrders()
const { clients, fetchClients, loading: clientsLoading, createClient } = useClients()

const form = ref({
  date: new Date().toISOString().split('T')[0],
  client_id: '',
  item_name: '',
  quantity: 1,
  client_order_no: '',   // 客戶單號/製通單號 (可選)
  
  // 印刷廠紙本專屬欄位
  paper_weight: '',     // 紙磅 (例如 "150g", "50g")
  paper_type: '',       // 紙別 (例如 "雙銅", "道林")
  cut_type: '',         // 裁別 (例如 "菊全開", "四開", "八開")
  front_side: null,     // 正面 (數字，例如 4, 1, 0)
  back_side: null,      // 反面 (數字，例如 1, 0)
  operator: null,       // 領機 (人數，數字)
  notes: '',            // 備註 (其他特殊要求/後加工)

  // 費用結構
  paper_fee: 0,
  plate_fee: 0,
  wage: 0,
})

const errors = ref({})
const submitting = ref(false)

// New Client Modal State
const showClientModal = ref(false)
const newClientForm = ref({
  name: '',
  tax_id: '',
  billing_cycle: 15,
})
const newClientErrors = ref({})
const creatingClient = ref(false)

const totalAmount = computed(() => {
  return (form.value.paper_fee + form.value.plate_fee + form.value.wage) * form.value.quantity
})

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

const validateForm = () => {
  errors.value = {}
  if (!form.value.date) errors.value.date = '請選擇日期'
  if (!form.value.client_id) errors.value.client_id = '請選擇客戶'
  if (!form.value.item_name.trim()) errors.value.item_name = '請輸入品名'
  if (form.value.quantity < 1) errors.value.quantity = '數量至少為 1'
  // 驗證正面/反面不能為負數
  if (form.value.front_side !== null && form.value.front_side < 0) errors.value.front_side = '不能為負數'
  if (form.value.back_side !== null && form.value.back_side < 0) errors.value.back_side = '不能為負數'
  if (form.value.operator !== null && form.value.operator < 0) errors.value.operator = '人數不能為負數'
  return Object.keys(errors.value).length === 0
}

const validateNewClient = () => {
  newClientErrors.value = {}
  if (!newClientForm.value.name.trim()) newClientErrors.value.name = '請輸入客戶名稱'
  if (newClientForm.value.tax_id && newClientForm.value.tax_id.length !== 8) {
    newClientErrors.value.tax_id = '統編需為 8 碼'
  }
  return Object.keys(newClientErrors.value).length === 0
}

const handleSubmit = async () => {
  if (!validateForm()) return

  submitting.value = true
  try {
    await createWorkOrder({
      date: form.value.date,
      client_id: Number(form.value.client_id),
      item_name: form.value.item_name.trim(),
      quantity: form.value.quantity,
      client_order_no: form.value.client_order_no || null,
      paper_weight: form.value.paper_weight || null,
      paper_type: form.value.paper_type || null,
      cut_type: form.value.cut_type || null,
      front_side: form.value.front_side,
      back_side: form.value.back_side,
      operator: form.value.operator,
      notes: form.value.notes || null,
      paper_fee: form.value.paper_fee,
      plate_fee: form.value.plate_fee,
      wage: form.value.wage,
    })
    router.push('/')
  } catch (err) {
    const detail = err.response?.data?.detail
    if (detail) {
      alert(detail)
    } else {
      alert('建立工單失敗，請稍後再試')
    }
  } finally {
    submitting.value = false
  }
}

const openClientModal = () => {
  newClientForm.value = { name: '', tax_id: '', billing_cycle: 15 }
  newClientErrors.value = {}
  showClientModal.value = true
}

const closeClientModal = () => {
  showClientModal.value = false
  newClientForm.value = { name: '', tax_id: '', billing_cycle: 15 }
  newClientErrors.value = {}
}

const handleCreateClient = async () => {
  if (!validateNewClient()) return

  creatingClient.value = true
  try {
    const newClient = await createClient({
      name: newClientForm.value.name.trim(),
      tax_id: newClientForm.value.tax_id || null,
      billing_cycle: newClientForm.value.billing_cycle,
    })
    // Auto-select the newly created client
    form.value.client_id = String(newClient.id)
    closeClientModal()
  } catch (err) {
    const detail = err.response?.data?.detail
    if (detail) {
      alert(detail)
    } else {
      alert('建立客戶失敗，請稍後再試')
    }
  } finally {
    creatingClient.value = false
  }
}

const resetForm = () => {
  form.value = {
    date: new Date().toISOString().split('T')[0],
    client_id: '',
    item_name: '',
    quantity: 1,
    client_order_no: '',
    paper_weight: '',
    paper_type: '',
    cut_type: '',
    front_side: null,
    back_side: null,
    operator: null,
    notes: '',
    paper_fee: 0,
    plate_fee: 0,
    wage: 0,
  }
  errors.value = {}
}

onMounted(() => {
  fetchClients()
})
</script>

<template>
  <AppLayout title="新增工單" :showBack="true" :fabAction="null">
    <template #default>
      <form @submit.prevent="handleSubmit" class="p-3 space-y-4" novalidate>
        <!-- Date Picker -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">工單日期</label>
          <input
            v-model="form.date"
            type="date"
            class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            :class="{ 'border-red-500': errors.date }"
            required
          />
          <p v-if="errors.date" class="mt-1 text-sm text-red-600">{{ errors.date }}</p>
        </div>

        <!-- Client Select with New Client Button -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-sm font-medium text-gray-700">客戶名稱</label>
            <button
              type="button"
              @click="openClientModal"
              class="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 touch-target px-2 py-1"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              新增客戶
            </button>
          </div>
          <select
            v-model="form.client_id"
            class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none"
            :class="{ 'border-red-500': errors.client_id }"
            required
          >
            <option value="" disabled>請選擇客戶</option>
            <option v-for="client in clients" :key="client.id" :value="client.id">
              {{ client.name }}
            </option>
          </select>
          <p v-if="errors.client_id" class="mt-1 text-sm text-red-600">{{ errors.client_id }}</p>
        </div>

        <!-- Item Name -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">品名</label>
          <input
            v-model="form.item_name"
            type="text"
            class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            :class="{ 'border-red-500': errors.item_name }"
            placeholder="例如：名片、傳單、海報"
            required
            autocomplete="off"
          />
          <p v-if="errors.item_name" class="mt-1 text-sm text-red-600">{{ errors.item_name }}</p>
        </div>

        <!-- Quantity -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">數量(令)</label>
          <input
            v-model.number="form.quantity"
            type="number"
            min="1"
            class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            :class="{ 'border-red-500': errors.quantity }"
            required
          />
          <p v-if="errors.quantity" class="mt-1 text-sm text-red-600">{{ errors.quantity }}</p>
        </div>

        <!-- 客戶單號 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">客戶單號 <span class="text-gray-400 text-xs font-normal">(選填)</span></label>
          <input
            v-model="form.client_order_no"
            type="text"
            class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="客戶的製通單號 / 訂單編號"
            autocomplete="off"
          />
        </div>

        <!-- 印刷規格區塊 -->
        <fieldset class="border border-gray-200 rounded-xl p-4 space-y-3 bg-gray-50">
          <legend class="text-sm font-medium text-gray-700">印刷規格</legend>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-gray-500 mb-1">紙磅</label>
              <input
                v-model="form.paper_weight"
                type="text"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="例如：150g, 200g, 100lb"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">紙別</label>
              <input
                v-model="form.paper_type"
                type="text"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="例如：雙銅, 道林, 米紙"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">裁別</label>
              <input
                v-model="form.cut_type"
                type="text"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="例如：菊全開, 四開, 八開"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">正面</label>
              <input
                v-model.number="form.front_side"
                type="number"
                min="0"
                step="1"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0"
                :class="{ 'border-red-500': errors.front_side }"
              />
              <p v-if="errors.front_side" class="mt-1 text-sm text-red-600">{{ errors.front_side }}</p>
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">反面</label>
              <input
                v-model.number="form.back_side"
                type="number"
                min="0"
                step="1"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0"
                :class="{ 'border-red-500': errors.back_side }"
              />
              <p v-if="errors.back_side" class="mt-1 text-sm text-red-600">{{ errors.back_side }}</p>
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">領機</label>
              <input
                v-model.number="form.operator"
                type="number"
                min="0"
                step="1"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0"
                :class="{ 'border-red-500': errors.operator }"
              />
              <p v-if="errors.operator" class="mt-1 text-sm text-red-600">{{ errors.operator }}</p>
            </div>
            <div class="col-span-2">
              <label class="block text-xs text-gray-500 mb-1">備註</label>
              <textarea
                v-model="form.notes"
                rows="2"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                placeholder="特殊要求、後加工說明..."
              />
            </div>
          </div>
        </fieldset>

        <!-- Fee Section -->
        <fieldset class="border border-gray-200 rounded-xl p-4 space-y-3 bg-gray-50">
          <legend class="text-sm font-medium text-gray-700">費用明細（單價）</legend>

          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-xs text-gray-500 mb-1">紙費</label>
              <input
                v-model.number="form.paper_fee"
                type="number"
                min="0"
                step="1"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">版費</label>
              <input
                v-model.number="form.plate_fee"
                type="number"
                min="0"
                step="1"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">印工</label>
              <input
                v-model.number="form.wage"
                type="number"
                min="0"
                step="1"
                class="w-full touch-target border border-gray-300 rounded-lg px-3 py-2.5 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0"
              />
            </div>
          </div>
        </fieldset>

        <!-- Total Amount Preview -->
        <div class="bg-primary-50 border border-primary-200 rounded-xl p-4">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-primary-800">預估總金額</span>
            <span class="text-2xl font-bold text-primary-700">{{ formatCurrency(totalAmount) }}</span>
          </div>
          <p class="text-xs text-primary-600 mt-1">
            計算方式：(紙費 + 版費 + 印工) × 數量 = ({{ form.paper_fee }} + {{ form.plate_fee }} + {{ form.wage }}) × {{ form.quantity }}
          </p>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="submitting"
          class="w-full touch-target bg-primary-600 text-white font-semibold rounded-xl py-3.5 active:scale-[0.98] transition-transform disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <svg v-if="submitting" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span>{{ submitting ? '建立中...' : '建立工單' }}</span>
        </button>

        <!-- Reset Button -->
        <button
          type="button"
          @click="resetForm"
          :disabled="submitting"
          class="w-full touch-target bg-white border border-gray-300 text-gray-700 font-medium rounded-xl py-3.5 active:bg-gray-50 transition-colors disabled:opacity-50"
        >
          重置表單
        </button>
      </form>

      <!-- New Client Modal -->
      <Teleport to="body">
        <div v-if="showClientModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="closeClientModal">
          <div class="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden animate-slide-up">
            <!-- Modal Header -->
            <div class="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 class="text-lg font-semibold text-gray-900">新增客戶</h2>
              <button
                @click="closeClientModal"
                :disabled="creatingClient"
                class="text-gray-400 hover:text-gray-600 touch-target p-1"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Modal Body -->
            <div class="p-4 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">客戶名稱 <span class="text-red-500">*</span></label>
                <input
                  v-model="newClientForm.name"
                  type="text"
                  class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  :class="{ 'border-red-500': newClientErrors.name }"
                  placeholder="例如：台積電、鴻海精密"
                  required
                  autocomplete="off"
                  @keydown.enter.prevent
                />
                <p v-if="newClientErrors.name" class="mt-1 text-sm text-red-600">{{ newClientErrors.name }}</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">統一編號 (選填)</label>
                <input
                  v-model="newClientForm.tax_id"
                  type="text"
                  maxlength="8"
                  class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  :class="{ 'border-red-500': newClientErrors.tax_id }"
                  placeholder="8 碼統編"
                  @keydown.enter.prevent
                />
                <p v-if="newClientErrors.tax_id" class="mt-1 text-sm text-red-600">{{ newClientErrors.tax_id }}</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">結帳日</label>
                <select
                  v-model.number="newClientForm.billing_cycle"
                  class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none"
                >
                  <option v-for="n in 31" :key="n" :value="n">{{ n }} 號</option>
                </select>
              </div>
            </div>

            <!-- Modal Footer -->
            <div class="p-4 border-t border-gray-200 bg-gray-50 flex gap-3">
              <button
                @click="closeClientModal"
                :disabled="creatingClient"
                class="flex-1 touch-target bg-white border border-gray-300 text-gray-700 font-medium rounded-xl py-3 active:bg-gray-50 transition-colors"
              >
                取消
              </button>
              <button
                @click="handleCreateClient"
                :disabled="creatingClient"
                class="flex-1 touch-target bg-primary-600 text-white font-semibold rounded-xl py-3 active:scale-[0.98] transition-transform disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <svg v-if="creatingClient" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>{{ creatingClient ? '建立中...' : '確認新增' }}</span>
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </template>
  </AppLayout>
</template>

<style scoped>
/* Custom select styling */
select.appearance-none {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 12px center;
  background-repeat: no-repeat;
  background-size: 16px;
  padding-right: 40px;
}

/* Number input spinner styling */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="number"] {
  -moz-appearance: textfield;
}

/* Modal animation */
@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: slide-up 0.25s ease-out;
}

/* Focus visible for accessibility */
:focus-visible {
  outline: 2px solid #14b8a6;
  outline-offset: 2px;
}
</style>