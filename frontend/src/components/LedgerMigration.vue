<script setup>
import { computed, ref, watch } from 'vue'
import api from '@/services/api'
const props = defineProps({ clients: Array })
const emit = defineEmits(['imported'])
const clientId = ref(''), rows = ref([]), busy = ref(false), message = ref('')
watch(() => props.clients, list => {
  if (!clientId.value) clientId.value = list.find(c => c.name === '南一書局')?.id || ''
}, {immediate:true})
const selected = computed(() => rows.value.filter(r => r.include))
const stages = ['排印','印製中','已完成_待請款','已請款']
async function read(event) {
  const files = Array.from(event.target.files)
  event.target.value = ''
  if (!files.length) return
  if (files.length > 100) {message.value='每批最多 100 份';return}
  busy.value = true
  message.value = ''
  rows.value = []
  try {
    for (const file of files) {
      try {
        if (file.size > 2000000) throw new Error('檔案超過 2 MB')
        const {data} = await api.post('/work-orders/excel-preview',file,{headers:{'Content-Type':'application/octet-stream'}})
        const f = data.fields
        const empty = !f.date && !f.item_name && !f.client_order_no && !data.totals.some(t => t.reams)
        rows.value.push({...data, name:file.name, include:!empty, empty, status:''})
      } catch(e) {
        rows.value.push({name:file.name,error:e.response?.data?.detail || e.message,include:false})
      }
    }
  } finally {busy.value = false}
}
async function save() {
  if (busy.value || !selected.value.length) return
  busy.value = true
  try {
    const orders = selected.value.map(r => ({...r.fields,client_id:clientId.value,
      status:r.status,source_hash:r.source_hash}))
    const {data} = await api.post('/work-orders/migrate',{orders})
    message.value = '已匯入 '+data.added.length+' 張，略過重複 '+data.skipped.length+' 張。'
    rows.value = []
    emit('imported')
  } catch(e) {
    const detail=e.response?.data?.detail
    message.value=typeof detail==='string' ? detail : '匯入未確認，請核對資料後重試。'
  } finally {busy.value=false}
}
</script>
<template>
<details class="paper-fold migration">
  <summary>舊工單 Excel 批次遷移</summary>
  <form @submit.prevent="save">
    <fieldset :disabled="busy">
      <label>匯入到客戶<select required v-model="clientId"><option value="">請選擇</option><option v-for="c in clients" :key="c.id" :value="c.id">{{c.name}}</option></select></label>
      <label>選取已填寫的南一工單（可多選）<input type="file" accept=".xlsx" multiple @change="read"></label>
      <p v-if="rows.length">請核對狀態與計價數量。三種範本提供用紙令數，缺少單價的工單以 0 元匯入，可在工單補登。</p>
      <article v-for="(r,i) in rows" :key="i">
        <b>{{r.name}}</b>
        <p v-if="r.error" role="alert">{{r.error}}</p>
        <p v-else-if="r.empty">空白範本，略過匯入。</p>
        <template v-else>
          <label><input type="checkbox" v-model="r.include"> 匯入這張 · {{r.template}}</label>
          <p>{{r.fields.client_order_no}}　<span v-for="t in r.totals" :key="t.label">{{t.label}} {{t.reams || '—'}} 令　</span></p>
          <fieldset v-if="r.include" class="fields">
            <label>品名<input v-model.trim="r.fields.item_name" required maxlength="200"></label>
            <label>訂單日期<input v-model="r.fields.date" type="date" required></label>
            <label>計價數量<input v-model.number="r.fields.quantity" type="number" min="1" step="1" required></label>
            <label>原工單狀態<select required v-model="r.status"><option value="">請核對</option><option v-for="s in stages" :key="s" :value="s">{{s.replace('_','・')}}</option></select></label>
          </fieldset>
          <p v-for="warning in r.warnings" :key="warning">{{warning}}</p>
        </template>
      </article>
      <button v-if="selected.length" class="new-order" type="submit">確認匯入 {{selected.length}} 張工單</button>
    </fieldset>
    <p role="status">{{busy ? '處理中…' : message}}</p>
  </form>
</details>
</template>
<style scoped>
form{padding:1rem;background:#faf8f0}label{display:block;margin:.5rem 0;font-weight:650}
input:not([type=checkbox]),select{display:block;max-width:100%;min-height:48px;border:1px solid #747a71;padding:.4rem;background:#fffdf6}
article{padding:1rem 0;border-top:1px solid #abaea5}.fields{display:flex;gap:1rem;flex-wrap:wrap}
</style>
