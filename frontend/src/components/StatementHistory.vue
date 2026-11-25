<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '@/services/api'
const rows = ref([]), chosen = ref([]), detail = ref(null), error = ref(''), busy = ref(false)
const month = ref(''), client = ref('')
const visible = computed(() => rows.value.filter(r => (!month.value || r.month === month.value) && (!client.value || r.client_name.includes(client.value))))
async function load() {
  error.value = ''
  try { rows.value = (await api.get('/reconciliation/statements')).data }
  catch { error.value = '無法載入結算單，請重新整理' }
}
async function merge() {
  if (!window.confirm('合併所選單據？原單會保留，並標示已併入新單。')) return
  busy.value = true
  try {
    const result = await api.post('/reconciliation/statements/merge', {ids: chosen.value})
    chosen.value = []
    await load()
    detail.value = result.data
  } catch (e) { error.value = e.response?.data?.detail || '併單失敗' }
  finally { busy.value = false }
}
const printSheet = () => window.print()
defineExpose({load})
onMounted(load)
</script>
<template>
<section class="history">
  <h2>歷史結算單</h2>
  <div class="tools"><label>客戶 <input v-model="client" @input="chosen=[]" placeholder="客戶名稱"></label>
    <label>帳期 <input type="month" v-model="month" @input="chosen=[]"></label>
    <button :disabled="busy || chosen.length < 2" @click="merge">合併所選單據（{{ chosen.length }}）</button>
  </div>
  <p v-if="error" role="alert">{{ error }} <button @click="load">重新載入</button></p>
  <p v-else-if="!visible.length">沒有符合的結算單</p>
  <div v-for="r in visible" :key="r.id" class="record">
    <label><input v-model="chosen" type="checkbox" :value="r.id" :disabled="!!r.merged_into"> #{{ r.id }}　{{ r.client_name }}　{{ r.month }}</label>
    <span>{{ r.total }} 元 · {{ r.merged_into ? '已併入 #'+r.merged_into : r.sources.length ? '合併單' : '分批單' }}</span>
    <button @click="detail=r">查看／列印</button>
  </div>
  <Teleport to="body"><div v-if="detail" class="statement-overlay" @keydown.esc="detail=null">
    <article class="statement-paper" role="dialog" aria-label="結算單">
      <div class="tools"><button @click="detail=null" autofocus>關閉</button><button @click="printSheet">列印／另存 PDF</button></div>
      <h2>{{ detail.sources.length ? '合併結算單' : '結算單' }} #{{ detail.id }}</h2>
      <p>{{ detail.client_name }} ｜ {{ detail.month }} ｜ 開單日 {{ detail.issued }}</p>
      <p>帳期 {{ detail.period_start }} 至 {{ detail.period_end }}</p>
      <p v-if="detail.sources.length">來源單號：{{ detail.sources.join('、') }}</p>
      <p v-if="detail.merged_into">本單已併入 #{{ detail.merged_into }}</p>
      <table><thead><tr><th>工單／日期</th><th>品名／客戶單號</th><th>數量</th><th>金額</th></tr></thead>
      <tbody><tr v-for="line in detail.lines" :key="line.order_id"><td>#{{ line.order_id }} · {{ line.date }}</td><td>{{ line.item }} {{ line.reference }}</td><td>{{ line.quantity }}</td><td>{{ line.amount }}</td></tr></tbody></table>
      <strong>合計新台幣 {{ detail.total }} 元</strong>
    </article></div></Teleport>
</section>
</template>
<style>
.history,.statement-paper{background:white;padding:1.2rem;border:1px solid #bbb}.history h2,.statement-paper h2{font-size:1.4rem;font-weight:750}.tools,.record{display:flex;flex-wrap:wrap;align-items:center;gap:.75rem;padding:.6rem 0}.record{border-top:1px solid #ddd}.tools input,.tools button,.record button{border:1px solid #aaa;padding:.45rem}.tools button:disabled{opacity:.45}.statement-overlay{position:fixed;inset:0;z-index:100;background:#3339;overflow:auto;padding:4vw}.statement-paper{max-width:850px;margin:auto}.statement-paper table{width:100%;margin:1rem 0}.statement-paper th,.statement-paper td{text-align:left;border-bottom:1px solid #aaa;padding:.45rem;overflow-wrap:anywhere}
@media print{body:has(.statement-overlay) #app,.statement-paper .tools{display:none}.statement-overlay{position:static;padding:0;overflow:visible;background:white}.statement-paper{border:none;max-width:none}.statement-paper tr{break-inside:avoid}}
</style>
