<script setup>
import { ref } from 'vue'
import api from '@/services/api'
const emit = defineEmits(['apply'])
const busy = ref(false), error = ref(''), result = ref(null)
const labels = {date:'工單日期',item_name:'品名',client_order_no:'客戶單號',paper_weight:'紙磅'}
async function scan(e) {
  const file=e.target.files[0]
  if(!file) return
  error.value=''; result.value=null; busy.value=true
  try {
    if(file.size>12*1024*1024) throw new Error('照片上限為 12 MB')
    const response=await api.post('/photos/recognize',file,{headers:{'Content-Type':'application/octet-stream'},timeout:120000})
    result.value=response.data
  } catch(err) {error.value=err.response?.data?.detail || err.message || '辨識失敗'}
  finally {busy.value=false;e.target.value=''}
}
</script>
<template><section class="border p-3 space-y-2">
<label class="block font-semibold">拍攝或上傳工單照片
<input class="block mt-2" :disabled="busy" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic" @change="scan"></label>
<p role="status" v-if="busy">正在本機辨識…</p><p role="alert" v-if="error">{{error}}</p>
<template v-if="result"><p>請核對候選值；數量、計價與承作項目請另行確認。</p>
<label v-for="(_,key) in result.fields" :key="key" class="block">{{labels[key]}} <input class="border" v-model="result.fields[key]"></label>
<details><summary>辨識原文（{{result.texts.length}} 段）</summary><p class="whitespace-pre-wrap">{{result.texts.join('\n')}}</p></details>
<button type="button" class="text-blue-700" @click="emit('apply',result.fields);result=null">帶入已核對欄位</button></template>
</section></template>
