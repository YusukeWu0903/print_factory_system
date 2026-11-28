<script setup>
import api from '@/services/api'
import { dataMode } from '@/services/dataMode'
import LedgerMigration from '@/components/LedgerMigration.vue'
import CombinedOrder from "@/components/CombinedOrder.vue"
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import {customerFields,shopFields} from '@/services/paperSections'
import OrderAudit from '@/components/OrderAudit.vue'
import OrderNotes from '@/components/OrderNotes.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useWorkOrders, useClients, useStatusHelpers } from '@/composables/useApi'

const router = useRouter()
const { workOrders, loading, error, fetchWorkOrders, updateWorkOrderStatus } = useWorkOrders()
const { clients, fetchClients } = useClients()
const { getStatusClass, getStatusLabel, nextStatus } = useStatusHelpers()

const exporting = ref(false)
async function downloadLedger() {
  exporting.value = true
  try {
    const {data} = await api.get('/work-orders/ledger.xlsx', {responseType:'blob', timeout:120000})
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    const date = new Date().toLocaleDateString('sv-SE', {timeZone:'Asia/Taipei'})
    link.download = (dataMode.value === 'sandbox' ? '測試' : '正式') + '工單總表-' + date + '.xlsx'
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 10000)
  } catch {
    alert('匯出失敗，請重新下載工單總表。')
  } finally {
    exporting.value = false
  }
}
const activeFilter = ref('all')
const route = useRoute()
const reviewOrders = computed(() => route.query.samples ? workOrders.value.filter(w => String(route.query.samples).split(',').includes(String(w.id))) : workOrders.value)
const counts = computed(() => {
  const result = { all: reviewOrders.value.length }
  for (const order of reviewOrders.value) result[order.status] = (result[order.status] || 0) + 1
  return result
})

const filters = [
  { key: 'all', label: '全部' },
  { key: '排印', label: '排印' },
  { key: '印製中', label: '印製中' },
  { key: '已完成_待請款', label: '待請款' },
  { key: '已請款', label: '已請款' },
]

const filteredWorkOrders = computed(() => {
  if (activeFilter.value === 'all') return reviewOrders.value
  return reviewOrders.value.filter(wo => wo.status === activeFilter.value)
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
  <AppLayout title="工單工作台" :showBack="false" :fabAction="() => router.push('/create')" fabLabel="新增工單">
    <template #default>
      <RouterLink class="edit-order mb-4" to="/progress">客戶進度表</RouterLink>
      <button class="edit-order mb-4 ml-2" :disabled="exporting" @click="downloadLedger">{{ exporting ? '正在匯出…' : '匯出全部工單 Excel' }}</button>
      <LedgerMigration :clients="clients" @imported="loadData" />
      <section v-if="!loading && !error" class="status-grid" aria-label="依狀態篩選工單">
        <button v-for="filter in filters" :key="filter.key" type="button"
          :aria-pressed="activeFilter === filter.key" @click="activeFilter = filter.key">
          <span>{{ filter.label }}</span><strong>{{ counts[filter.key] || 0 }} <small>筆</small></strong>
          <span class="meter" aria-hidden="true"><i :style="{ width: ((counts[filter.key] || 0) / (counts.all || 1) * 100) + '%' }" /></span>
        </button>
      </section>

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
      <div v-else class="register">
        <div v-if="filteredWorkOrders.length === 0" class="text-center py-12 text-gray-400">
          <svg class="w-16 h-16 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p class="text-sm">{{ activeFilter === 'all' ? '尚無工單，點選「新增工單」開始' : '此狀態下無工單' }}</p>
        </div>

        <div v-else>
          <article
            v-for="wo in filteredWorkOrders"
            :key="wo.id"
            class="job">
            <header class="order-head"><div>
              <p class="order-ref">工單 #{{ wo.id }}<span v-if="wo.client_order_no">　·　客戶單號 {{ wo.client_order_no }}</span></p>
              <h3>{{ wo.item_name }}</h3>
            </div><StatusBadge :key="wo.status" :status="wo.status" /></header>
            <dl class="order-facts">
              <div><dt>客戶</dt><dd>{{ clientMap[wo.client_id] || wo.client_name }}</dd></div>
              <div><dt>工單日期</dt><dd>{{ wo.date }}</dd></div>
              <div v-if="!wo.combined"><dt>完成數量</dt><dd>{{wo.completed_quantity ?? '尚未填報'}}</dd></div><div><dt>工單數量</dt><dd>{{ wo.quantity.toLocaleString('zh-TW') }}</dd></div>
              <div><dt>工單金額</dt><dd>{{ formatCurrency(wo.total_amount) }}</dd></div>
            </dl>
            <CombinedOrder v-if="wo.combined" :spec="wo.combined" :reports="wo.piece_reports" />
            <details class="paper-fold"><summary>客戶來單資料</summary>
              <p>入紙：{{[wo.paper_weight,wo.paper_type,wo.cut_type].filter(Boolean).join(' · ') || '未填'}}</p>
              <div v-if="wo.ocr_review_notes"><b>辨識待整理備註</b><p class="whitespace-pre-wrap">{{wo.ocr_review_notes}}</p></div>
              <p v-for="(label,key) in customerFields" :key="key">{{label}}：{{wo[key] || '未填'}}</p>
            </details>
            <details class="paper-fold"><summary>廠內作業資料</summary>
              <p v-for="(label,key) in shopFields" :key="key">{{label}}：{{wo[key] || '未填'}}</p>
              <p>正面 {{wo.front_side ?? '—'}} 色 · 反面 {{wo.back_side ?? '—'}} 色 · 人員 {{wo.operator ?? '—'}} 人</p>
              <OrderNotes v-if="wo.notes" :notes="wo.notes" />
            </details>
            <OrderAudit :order="wo" /><footer class="order-footer"><RouterLink class="edit-order" :to="{ path: '/create', query: { edit: wo.id, samples: route.query.samples } }">編輯工單</RouterLink><button v-if="nextStatus(wo.status)" @click="handleStatusChange(wo)">更新為{{ getStatusLabel(nextStatus(wo.status)) }} →</button></footer>
          </article>
        </div>
      </div>
    </template>
  </AppLayout>
</template>
