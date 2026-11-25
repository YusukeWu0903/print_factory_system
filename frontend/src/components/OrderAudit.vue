<script setup>
import { ref, watch } from 'vue'
import api from '@/services/api'
const props = defineProps({order:Object})
const opened=ref(false), entries=ref([]), error=ref(''), loading=ref(false)
const labels={date:'日期',client_id:'客戶編號',item_name:'品名',quantity:'數量',client_order_no:'客戶單號',paper_weight:'紙磅',paper_type:'紙別',cut_type:'裁別',front_side:'正面色數',back_side:'反面色數',operator:'人員',notes:'備註',paper_fee:'紙錢',plate_fee:'版費',wage:'印工',total_amount:'總金額',status:'狀態'}
const time=t=>new Date(t).toLocaleString('zh-TW',{timeZone:'Asia/Taipei',hour12:false})
async function load(){
  if(!opened.value)return
  loading.value=true;error.value=''
  try{entries.value=(await api.get('/work-orders/'+props.order.id+'/history')).data}
  catch{error.value='無法載入紀錄，請重試'}
  finally{loading.value=false}
}
watch(()=>props.order.revision,load)
</script>
<template><div class="audit"><span>最後更新（台灣時間）　{{order.updated_at ? time(order.updated_at) : '尚無時間紀錄'}}</span>
<details @toggle="opened=$event.target.open;load()"><summary>編輯紀錄</summary>
<p v-if="loading">載入中…</p><button v-else-if="error" @click="load">{{error}}</button>
<p v-else-if="!entries.length">啟用紀錄後尚無變更。</p>
<ol v-else><li v-for="e in entries" :key="e.id"><b>{{e.action}}</b> · {{time(e.timestamp)}} · {{e.actor}}
<div v-for="(pair,key) in e.changes" :key="key"><strong>{{labels[key] || key}}</strong>　原值：{{pair[0] ?? '未填'}} → 新值：{{pair[1] ?? '未填'}}</div></li></ol></details></div></template>
<style scoped>.audit{margin-top:14px;padding-top:10px;border-top:1px solid #ddd;font-size:14px;color:#43464a}.audit summary{cursor:pointer;color:#173ba9;padding:8px 0}.audit li{padding:8px 0;border-top:1px solid #ddd}.audit li div{white-space:pre-wrap;overflow-wrap:anywhere;padding:3px 0}</style>
