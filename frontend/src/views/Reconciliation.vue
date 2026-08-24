<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { useWorkOrders, useClients, useStatusHelpers } from '@/composables/useApi'

const router = useRouter()
const { clients, fetchClients } = useClients()
const { updateWorkOrderStatus } = useWorkOrders()
const { getStatusLabel } = useStatusHelpers()

// 狀態
const selectedMonth = ref('')
const selectedClientId = ref('')
const loading = ref(false)
const error = ref(null)
const reconciliationData = ref(null)
const availableMonths = ref([])
const confirming = ref(false)
const selectedWorkOrders = ref([])

// 可用月份清單
const loadMonths = async () => {
  if (!selectedClientId.value) {
    availableMonths.value = []
    selectedMonth.value = ''
    return
  }
  try {
    const response = await fetch(`/api/reconciliation/months?client_id=${selectedClientId.value}`)
    if (response.ok) {
      availableMonths.value = await response.json()
      if (availableMonths.value.length > 0) {
        selectedMonth.value = availableMonths.value[0] // 預設選最新月份
      }
    }
  } catch (err) {
    console.error('載入月份失敗:', err)
  }
}

// 載入對帳彙總
const loadSummary = async () => {
  if (!selectedMonth.value || !selectedClientId.value) return
  
  loading.value = true
  error.value = null
  reconciliationData.value = null
  
  try {
    const response = await fetch(`/api/reconciliation/summary?month=${selectedMonth.value}&client_id=${selectedClientId.value}`)
    if (response.ok) {
      reconciliationData.value = await response.json()
    } else {
      const err = await response.json()
      throw new Error(err.detail || '載入對帳資料失敗')
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// 切換工單選取
const toggleWorkOrder = (id) => {
  const idx = selectedWorkOrders.value.indexOf(id)
  if (idx === -1) {
    selectedWorkOrders.value.push(id)
  } else {
    selectedWorkOrders.value.splice(idx, 1)
  }
}

// 全選/取消全選
const toggleAllWorkOrders = () => {
  if (selectedWorkOrders.value.length === reconciliationData.value?.work_orders.length) {
    selectedWorkOrders.value = []
  } else {
    selectedWorkOrders.value = reconciliationData.value.work_orders.map(wo => wo.id)
  }
}

// 確認結帳
const handleConfirm = async () => {
  if (selectedWorkOrders.value.length === 0) {
    alert('請至少選擇一張工單')
    return
  }
  
  if (!confirm(`確定將 ${selectedWorkOrders.value.length} 張工單標記為「已請款」？此操作不可復原。`)) {
    return
  }
  
  confirming.value = true
  try {
    const response = await fetch('/api/reconciliation/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        month: selectedMonth.value,
        client_id: selectedClientId.value,
        work_order_ids: selectedWorkOrders.value
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      alert(result.message)
      selectedWorkOrders.value = []
      await loadSummary() // 重新載入資料
    } else {
      const err = await response.json()
      throw new Error(err.detail || '結帳失敗')
    }
  } catch (err) {
    alert(err.message)
  } finally {
    confirming.value = false
  }
}

// 格式化金額
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

// 格式化日期
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// 客戶變更時重置月份
const handleClientChange = () => {
  selectedMonth.value = ''
  reconciliationData.value = null
  selectedWorkOrders.value = []
  loadMonths()
}

// 月份變更時重新載入
const handleMonthChange = () => {
  selectedWorkOrders.value = []
  loadSummary()
}

// 初始化
onMounted(async () => {
  await fetchClients()
})

// 監聽客戶/月份變更
import { watch } from 'vue'
watch(selectedClientId, () => {
  handleClientChange()
})
watch(selectedMonth, () => {
  if (selectedMonth.value) loadSummary()
})
</script>

<template>
  <AppLayout title="月底對帳" :showBack="false">
    <template #default>
      <div class="p-3 space-y-4">
        <!-- 篩選區塊 -->
        <div class="bg-white rounded-xl shadow-sm border border-amber-50 p-4 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- 客戶選擇 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">客戶</label>
              <select
                v-model="selectedClientId"
                class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent appearance-none"
              >
                <option value="" disabled>請選擇客戶</option>
                <option v-for="client in clients" :key="client.id" :value="client.id">
                  {{ client.name }}
                </option>
              </select>
            </div>

            <!-- 月份選擇 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">對帳月份</label>
              <select
                v-model="selectedMonth"
                :disabled="!selectedClientId || availableMonths.length === 0"
                class="w-full touch-target border border-gray-300 rounded-lg px-4 py-3 text-base bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent appearance-none"
              >
                <option value="" disabled>請選擇月份</option>
                <option v-for="month in availableMonths" :key="month" :value="month">
                  {{ month }}
                </option>
              </select>
              <p v-if="!selectedClientId" class="mt-1 text-xs text-gray-500">請先選擇客戶</p>
              <p v-else-if="availableMonths.length === 0" class="mt-1 text-xs text-amber-600">該客戶無待請款月份</p>
            </div>
          </div>
        </div>

        <!-- 錯誤訊息 -->
        <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
          {{ error }}
        </div>

        <!-- 載入中 -->
        <div v-else-if="loading" class="flex items-center justify-center py-12">
          <div class="flex flex-col items-center gap-3">
            <div class="w-8 h-8 border-3 border-amber-500 border-t-transparent rounded-full animate-spin" />
            <span class="text-gray-500 text-sm">載入對帳資料...</span>
          </div>
        </div>

        <!-- 對帳內容 -->
        <div v-else-if="reconciliationData" class="space-y-4">
          <!-- 彙總資訊卡片 -->
          <div class="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-100 p-4">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="bg-white rounded-lg p-3 shadow-sm">
                <p class="text-xs text-gray-500">客戶</p>
                <p class="font-semibold text-gray-800">{{ reconciliationData.client_name }}</p>
              </div>
              <div class="bg-white rounded-lg p-3 shadow-sm">
                <p class="text-xs text-gray-500">月份</p>
                <p class="font-semibold text-gray-800">{{ reconciliationData.month }}</p>
              </div>
              <div class="bg-white rounded-lg p-3 shadow-sm">
                <p class="text-xs text-gray-500">工單筆數</p>
                <p class="font-semibold text-gray-800">{{ reconciliationData.work_order_count }} 筆</p>
              </div>
              <div class="bg-white rounded-lg p-3 shadow-sm">
                <p class="text-xs text-gray-500">總金額</p>
                <p class="font-bold text-amber-700 text-lg">{{ formatCurrency(reconciliationData.total_amount) }}</p>
              </div>
            </div>
          </div>

          <!-- 工單明細表格 -->
          <div class="bg-white rounded-xl shadow-sm border border-amber-50 overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-amber-50 border-b border-amber-100">
                  <tr>
                    <th class="w-12 px-3 py-2 text-center">
                      <input
                        type="checkbox"
                        :checked="selectedWorkOrders.length === reconciliationData.work_orders.length && reconciliationData.work_orders.length > 0"
                        :indeterminate="selectedWorkOrders.length > 0 && selectedWorkOrders.length < reconciliationData.work_orders.length"
                        @change="toggleAllWorkOrders"
                        class="w-5 h-5 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                      />
                    </th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">日期</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">品名</th>
                    <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">數量</th>
                    <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">規格</th>
                    <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider pr-3">金額</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr v-for="wo in reconciliationData.work_orders" :key="wo.id" class="hover:bg-amber-50/50">
                    <td class="px-3 py-3 text-center">
                      <input
                        type="checkbox"
                        :checked="selectedWorkOrders.includes(wo.id)"
                        @change="toggleWorkOrder(wo.id)"
                        class="w-5 h-5 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                      />
                    </td>
                    <td class="px-3 py-3 text-sm text-gray-900">{{ formatDate(wo.date) }}</td>
                    <td class="px-3 py-3 text-sm text-gray-900">{{ wo.item_name }}</td>
                    <td class="px-3 py-3 text-center text-sm text-gray-600">{{ wo.quantity }}</td>
                    <td class="px-3 py-3 text-center text-xs">
                      <div class="flex flex-col items-center gap-1">
                        <span v-if="wo.cut_type" class="bg-amber-50 text-amber-700 px-2 py-0.5 rounded text-xs">📐 {{ wo.cut_type }}</span>
                        <span v-if="wo.paper_type" class="bg-gray-50 text-gray-600 px-2 py-0.5 rounded text-xs">{{ wo.paper_type }}</span>
                        <span v-if="wo.paper_weight" class="bg-gray-50 text-gray-600 px-2 py-0.5 rounded text-xs">{{ wo.paper_weight }}</span>
                        <span v-if="wo.front_side !== null" class="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs">正 {{ wo.front_side }}色</span>
                        <span v-if="wo.back_side !== null" class="bg-green-50 text-green-700 px-2 py-0.5 rounded text-xs">反 {{ wo.back_side }}色</span>
                        <span v-if="wo.operator !== null" class="bg-purple-50 text-purple-700 px-2 py-0.5 rounded text-xs">👥 {{ wo.operator }}人</span>
                      </div>
                    </td>
                    <td class="px-3 py-3 text-right text-sm font-medium text-gray-800 pr-3">{{ formatCurrency(wo.total_amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 底部總計與操作 -->
            <div class="bg-gray-50 border-t border-amber-100 px-4 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
              <div class="flex items-center gap-4">
                <span class="text-sm text-gray-600">已選：</span>
                <span class="text-lg font-bold text-amber-700">{{ selectedWorkOrders.length }} / {{ reconciliationData.work_orders.length }} 筆</span>
                <span class="text-sm text-gray-600">金額：</span>
                <span class="text-lg font-bold text-amber-700">
                  {{ formatCurrency(
                    reconciliationData.work_orders
                      .filter(wo => selectedWorkOrders.includes(wo.id))
                      .reduce((sum, wo) => sum + wo.total_amount, 0)
                  ) }}
                </span>
              </div>
              
              <button
                :disabled="selectedWorkOrders.length === 0 || confirming"
                @click="handleConfirm"
                class="w-full md:w-auto touch-target bg-gradient-to-r from-amber-500 to-orange-500 text-white font-semibold rounded-xl py-3 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <svg v-if="confirming" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>{{ confirming ? '結帳中...' : '確認結帳' }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 空狀態 -->
        <div v-else class="text-center py-12 text-gray-400">
          <svg class="w-16 h-16 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p class="text-sm">
            <span v-if="!selectedClientId">請選擇客戶與月份開始對帳</span>
            <span v-else-if="availableMonths.length === 0">該客戶無待請款月份</span>
            <span v-else>該月份無待請款工單</span>
          </p>
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<style scoped>
/* Checkbox 樣式 */
input[type="checkbox"] {
  accent-color: #f59e0b;
}

/* 表格響應式 */
@media (max-width: 640px) {
  table {
    font-size: 0.875rem;
  }
  th, td {
    padding: 0.5rem 0.25rem !important;
  }
}

/* 動畫 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>