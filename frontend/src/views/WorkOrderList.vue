<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useWorkOrders, useClients, useStatusHelpers } from '@/composables/useApi'

const router = useRouter()
const { workOrders, loading, error, fetchWorkOrders, updateWorkOrderStatus } = useWorkOrders()
const { clients, fetchClients } = useClients()
const { getStatusClass, getStatusLabel, nextStatus } = useStatusHelpers()

const activeFilter = ref('all')
const showFilterMenu = ref(false)

const filters = [
  { key: 'all', label: '全部' },
  { key: '印製中', label: '印製中' },
  { key: '已完成_待請款', label: '待請款' },
  { key: '已請款', label: '已請款' },
]

const filteredWorkOrders = computed(() => {
  if (activeFilter.value === 'all') return workOrders.value
  return workOrders.value.filter(wo => wo.status === activeFilter.value)
})

const clientMap = computed(() => {
  const map = {}
  clients.value.forEach(c => { map[c.id] = c.name })
  return map
})

const handleStatusChange = async (workOrder) => {
  const newStatus = nextStatus(workOrder.status)
  if (!newStatus) return

  if (confirm(`確定將「${workOrder.item_name}」標記為「${getStatusLabel(newStatus)}」？`)) {
    try {
      await updateWorkOrderStatus(workOrder.id, newStatus)
    } catch (err) {
      alert(err.response?.data?.detail || '狀態更新失敗')
    }
  }
}

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const loadData = async () => {
  await Promise.all([fetchWorkOrders(), fetchClients()])
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <AppLayout title="工單列表" :showBack="false" :fabAction="() => router.push('/create')" fabLabel="新增工單">
    <template #default>
      <!-- Filter Tabs - Fixed at top with warm background -->
      <div class="sticky top-0 z-30 bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-100 px-3 py-2 shadow-sm">
        <div class="flex gap-2 overflow-x-auto pb-2 -mx-3 px-3" role="tablist" aria-label="工單狀態篩選">
          <button
            v-for="filter in filters"
            :key="filter.key"
            @click="activeFilter = filter.key"
            :class="[
              'touch-target px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
              activeFilter === filter.key
                ? 'bg-amber-600 text-white shadow-sm'
                : 'bg-white text-gray-700 hover:bg-amber-50 border border-amber-100'
            ]"
            role="tab"
            :aria-selected="activeFilter === filter.key"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="flex flex-col items-center gap-3">
          <div class="w-8 h-8 border-3 border-amber-500 border-t-transparent rounded-full animate-spin" />
          <span class="text-gray-500 text-sm">載入中...</span>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-4 text-center text-red-600 text-sm">
        {{ error }}
        <button @click="loadData" class="ml-2 text-amber-600 underline">重試</button>
      </div>

      <!-- Work Orders List -->
      <div v-else class="pb-24 space-y-3">
        <div v-if="filteredWorkOrders.length === 0" class="text-center py-12 text-gray-400">
          <svg class="w-16 h-16 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p class="text-sm">{{ activeFilter === 'all' ? '尚無工單，點擊右下角新增' : '此狀態下無工單' }}</p>
        </div>

        <div v-else class="space-y-3">
          <article
            v-for="wo in filteredWorkOrders"
            :key="wo.id"
            class="bg-white rounded-xl shadow-sm border border-amber-50 p-4 touch-target hover:shadow-md transition-shadow"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <h3 class="text-base font-semibold text-gray-800 truncate">{{ wo.item_name }}</h3>
                  <StatusBadge :status="wo.status" clickable @click="handleStatusChange(wo)" />
                </div>
                <div class="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                  <span class="flex items-center gap-1 bg-amber-50 px-2 py-1 rounded-lg">
                    <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    {{ clientMap[wo.client_id] || `客戶 #${wo.client_id}` }}
                  </span>
                  <span class="flex items-center gap-1 bg-amber-50 px-2 py-1 rounded-lg">
                    <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ formatDate(wo.date) }}
                  </span>
                </div>
                
                <!-- Print specs row -->
                <div class="mt-2 flex flex-wrap gap-2 text-xs">
                  <span v-if="wo.paper_weight" class="bg-gray-50 text-gray-600 px-2 py-0.5 rounded">{{ wo.paper_weight }}</span>
                  <span v-if="wo.paper_type" class="bg-gray-50 text-gray-600 px-2 py-0.5 rounded">{{ wo.paper_type }}</span>
                  <span v-if="wo.cut_type" class="bg-amber-50 text-amber-700 px-2 py-0.5 rounded font-medium">📐 {{ wo.cut_type }}</span>
                  <span v-if="wo.front_side !== null" class="bg-blue-50 text-blue-700 px-2 py-0.5 rounded">正 {{ wo.front_side }} 色</span>
                  <span v-if="wo.back_side !== null" class="bg-green-50 text-green-700 px-2 py-0.5 rounded">反 {{ wo.back_side }} 色</span>
                  <span v-if="wo.operator !== null" class="bg-purple-50 text-purple-700 px-2 py-0.5 rounded">👥 {{ wo.operator }} 人</span>
                </div>
                
                <p v-if="wo.notes" class="mt-1 text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded line-clamp-1">{{ wo.notes }}</p>
              </div>

              <div class="flex flex-col items-end gap-1 shrink-0">
                <span class="text-lg font-bold text-gray-800">{{ formatCurrency(wo.total_amount) }}</span>
                <span class="text-xs text-gray-400">數量：{{ wo.quantity }}</span>
              </div>
            </div>

            <!-- Status Action Button -->
            <button
              v-if="wo.status !== '已請款'"
              @click="handleStatusChange(wo)"
              class="mt-3 w-full touch-target bg-gradient-to-r from-amber-500 to-orange-500 text-white font-medium rounded-lg shadow-sm hover:from-amber-600 hover:to-orange-600 transition-all flex items-center justify-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              更新為：{{ getStatusLabel(nextStatus(wo.status)) }}
            </button>
          </article>
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<style scoped>
/* Ensure proper touch target sizing */
.touch-target {
  min-height: 48px;
}

/* Custom scrollbar hide for filter tabs */
.flex.gap-2.overflow-x-auto::-webkit-scrollbar {
  display: none;
}

/* Line clamp utility */
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Warm scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: #fef3e2;
}
::-webkit-scrollbar-thumb {
  background: #fbbf24;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #f59e0b;
}
</style>