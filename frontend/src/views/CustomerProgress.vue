<script setup>
import { computed, onMounted, ref } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { useClients, useWorkOrders } from '@/composables/useApi'
import { pieces } from '@/services/combined'

const { clients, fetchClients, error: clientError } = useClients()
const { workOrders, fetchWorkOrders, loading, error } = useWorkOrders()
const customer = ref('')
const month = ref('')
const name = computed(() => clients.value.find(c => c.id === customer.value)?.name)
const rows = computed(() => workOrders.value.filter(w =>
  w.client_id === customer.value && (!month.value || w.date.startsWith(month.value))))
const months = computed(() => [...new Set(workOrders.value.filter(w => w.client_id === customer.value)
  .map(w => w.date.slice(0,7)))].sort().reverse())
const fields = ['台數','本數','用料','紙種']
function specs(w) {
  if (!w.combined) return [[w.press_runs,w.book_count,w.paper_input,[w.paper_weight,w.paper_type].filter(Boolean).join(' ')]]
  return ['student','teacher','answer'].map(key => {
    const paper = key === 'answer' ? null : w.combined[key+'_paper']
    return [pieces[key]+' '+(w.combined[key].runs.map(r => r.presses).filter(Boolean).join('＋') || '—'),
      paper?.quantity,paper?.reams ? paper.reams+' 令' : '',paper?.paper]
  })
}
const refresh = () => Promise.all([fetchClients(),fetchWorkOrders()])
onMounted(refresh)
const print = () => window.print()
</script>
<template>
<AppLayout title="客戶進度表">
<section class="progress-report">
  <div class="controls">
    <label>客戶<select v-model="customer" @change="month=''"><option value="">請選擇客戶</option><option v-for="c in clients" :value="c.id" :key="c.id">{{c.name}}</option></select></label>
    <label>工單月份<select v-model="month" :disabled="!customer"><option value="">全部月份</option><option v-for="m in months" :key="m">{{m}}</option></select></label>
    <button class="edit-order" @click="refresh" :disabled="loading">重新載入</button>
    <button class="new-order" @click="print" :disabled="loading || !!error || !!clientError || !rows.length">列印／存成 PDF</button>
  </div>
  <p v-if="loading">正在載入進度…</p>
  <p v-else-if="error || clientError" role="alert">{{ error || clientError }}</p>
  <template v-else-if="name">
    <h2>{{name}}　生產進度表</h2><p>{{month || '全部月份'}} · 共 {{rows.length}} 張工單</p>
    <p v-if="!rows.length">目前沒有符合的工單。</p>
    <div v-else class="scroll"><table>
      <thead><tr><th>工單日期</th><th>編號</th><th>品名及規格</th><th>生產進度</th><th>交期</th><th>後加工</th></tr></thead>
      <tbody><tr v-for="w in rows" :key="w.id">
        <td>{{w.date}}</td><td><template v-if="w.plate_number">製版 {{w.plate_number}}<br></template>{{w.client_order_no ? '客戶 '+w.client_order_no : '工單 #'+w.id}}</td>
        <td><b>{{w.item_name}}</b><details><summary>印刷規格</summary>
          <ul v-for="(spec,i) in specs(w)" :key="i"><li v-for="(v,j) in spec" :key="j">{{fields[j]}}　{{v || '—'}}</li></ul>
        </details></td>
        <td><b>{{['已請款','已完成_待請款'].includes(w.status) ? '已完成' : w.status}}</b>
          <template v-if="w.combined"><p v-for="(label,key) in pieces" :key="key">{{label}} · {{w.piece_reports?.[key] == null ? '待回報' : '已回報 '+w.piece_reports[key]}}</p></template>
          <p v-else-if="w.completed_quantity != null">已回報 {{w.completed_quantity}}</p>
        </td><td>{{w.due_date || '—'}}</td><td>{{w.finisher || '—'}}</td>
      </tr></tbody>
    </table></div>
  </template>
</section>
</AppLayout>
</template>
<style scoped>
.controls{display:flex;gap:1rem;align-items:end;flex-wrap:wrap;padding:1rem;background:#e1e7df}
.controls select{display:block;min-height:48px;padding:.4rem;background:#fffdf6;border:1px solid #68736a;max-width:100%}
.controls button:disabled{opacity:.55}
h2{margin-top:1.25rem;font-size:1.5rem;font-weight:700}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;background:#faf8f0}
th,td{text-align:left;vertical-align:top;padding:.7rem;border-bottom:1px solid #aeb4ac}th{background:#dce6df}
summary{cursor:pointer;text-decoration:underline}ul{padding:.4rem 0;border-top:1px solid #c0c5bb}
@media(max-width:700px){table{min-width:46rem}}
@media print{
  :global(.mast),:global(.headline),.controls{display:none}
  :global(.sheet){width:100%;padding:0}.scroll{overflow:visible}
  table{min-width:0;font-size:10pt}tr{break-inside:avoid}h2{margin:0}
}
</style>
