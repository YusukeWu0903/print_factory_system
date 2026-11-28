<script setup>
import { computed, ref } from 'vue'
import { photoLabels as labels } from '@/services/photoFields'
import { splitPaperInput } from '@/services/paperInput'
import api from '@/services/api'
const emit = defineEmits(['apply','busy'])
const busy = ref(false), error = ref(''), result = ref(null)
const props = defineProps({ feedback: String, applyChoice: Function })
const target = ref(''), selectedText = ref(''), notice = ref(''), sourceIndex = ref('')
function choose(key,value) {
  target.value=key
  selectedText.value=value
  notice.value=''
}
function assign() {
  const key=target.value
  const value=selectedText.value.trim()
  if (!value || !key) return
  if (key==='date' && !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    notice.value='訂單日期請填西元年，例如 2026-11-27。'
    return
  }
  if (key==='paper_input' && !splitPaperInput(value).some(Boolean)) {
    notice.value='入紙數量請填令或張，例如 2 令＋100 張。'
    return
  }
  if (['front_side','back_side'].includes(key) && !/^\d+$/.test(value)) {
    notice.value='色數請填整數。'
    return
  }
  const applied=props.applyChoice({[key]:['front_side','back_side'].includes(key) ? Number(value) : value})
  notice.value=applied ? '已填入'+labels[key] : key==='client_name' ? '請確認此客戶已建檔，或直接在客戶欄選擇。' : '欄位已有資料，請到表單核對。'
}
const recognized = computed(() => {
  const fields = result.value?.fields || {}
  const pairs = Object.entries(labels).map(([key,label]) => [label,fields[key]])
  for (const [key,label] of [['student_paper','學用'],['teacher_paper','教用']]) {
    const paper = fields.combined?.[key]
    if (paper) pairs.push([label+'來單數量',paper.quantity],[label+'用紙',paper.paper])
  }
  return pairs.filter(([,value]) => value != null && value !== '')
})
async function scan(e) {
  const file=e.target.files[0]
  if(!file) return
  error.value=''; busy.value=true; emit('busy',true)
  try {
    if(file.size>12*1024*1024) throw new Error('照片上限為 12 MB')
    const response=await api.post('/photos/recognize',file,{headers:{'Content-Type':'application/octet-stream'},timeout:120000})
    sourceIndex.value=''; choose('','')
    result.value={...response.data, filename:file.name}
    emit('apply',response.data.fields,response.data.texts,response.data.mapped_lines)
  } catch(err) {error.value=err.response?.data?.detail || err.message || '辨識失敗'}
  finally {busy.value=false;emit('busy',false);e.target.value=''}
}
</script>
<template><section class="border p-3 space-y-2">
<label class="block font-semibold">拍攝或上傳工單照片
<input class="block mt-2" :disabled="busy" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic" @change="scan"></label>
<p role="status" v-if="busy">正在本機辨識…</p><p role="alert" v-if="error">{{error}}</p>
<template v-if="result">
<p role="status">{{feedback}}</p>
<div class="ocr-review">
  <h3>照片辨識結果</h3><p>{{result.filename}}</p>
  <dl><div v-for="[label,value] in recognized" :key="label"><dt>{{label}}</dt><dd>{{value}}</dd></div></dl>
</div>
<details :open="!!result.suggestions?.length">
  <summary>核對並指定欄位<span v-if="result.suggestions?.length">（{{result.suggestions.length}} 個建議）</span></summary>
  <button v-for="(s,i) in result.suggestions" :key="i" type="button" class="choice" @click="choose(s.key,s.value)">
    {{s.source}} → {{labels[s.key]}}
  </button>
  <label>選取辨識原文<select v-model="sourceIndex" @change="choose('', result.texts[sourceIndex] || '')">
    <option value="">請選擇文字</option><option v-for="(text,i) in result.texts" :key="i" :value="i">{{text}}</option>
  </select></label>
  <template v-if="selectedText || target || sourceIndex !== ''">
    <label>要填入的文字<input v-model="selectedText"></label>
    <label>填入欄位<select v-model="target"><option value="">請選擇欄位</option><option v-for="(label,key) in labels" :key="key" :value="key">{{label}}</option></select></label>
    <button class="edit-order" type="button" :disabled="busy || !target || !selectedText.trim()" @click="assign">填入選定欄位</button>
  </template>
  <p role="status">{{notice}}</p>
</details>
<details><summary>辨識原文（{{result.texts.length}} 段）</summary><p class="whitespace-pre-wrap">{{result.texts.join('\n')}}</p></details>
</template>
</section></template>

<style scoped>
.choice{display:block;text-align:left;padding:.6rem;border-bottom:1px solid #999;color:#234b34;overflow-wrap:anywhere}details label,details input,details select{display:block;width:100%;min-width:0;margin:.5rem 0}details input,details select{border:1px solid #71786f;padding:.4rem}
.ocr-review{padding:.75rem 1rem;background:#e9eee6;border-inline-start:4px solid #416653;overflow-wrap:anywhere}
h3,dt{font-weight:700}dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,12rem),1fr));gap:.5rem;margin-top:.5rem}
</style>
