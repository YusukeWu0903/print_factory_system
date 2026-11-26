<script setup>
import CombinedOrder from '@/components/CombinedOrder.vue'
import {pieces} from '@/services/combined'
import {ref,onMounted} from 'vue'
import {authState,logout} from '@/services/auth'
import {shopFields} from '@/services/paperSections'
import {staffRequest} from '@/services/staff'
const orders=ref([]),draft=ref({}),message=ref(''),busy=ref(false)
async function load(){
 try{orders.value=await staffRequest('orders');draft.value = {}
 for (const w of orders.value) {
   draft.value[w.id] = w.completed_quantity ?? ''
   for (const key of Object.keys(pieces)) draft.value[w.id + '-' + key] = w.piece_reports?.[key] ?? ''
 }}
 catch(e){message.value=e.message}
}
async function save(w, piece = null){
 if (busy.value) return
 const key = piece ? w.id + '-' + piece : w.id
 const quantity = Number(draft.value[key])
 busy.value=true
 try {
   const updated = await staffRequest('orders/'+w.id,'PATCH',{
     completed_quantity:quantity, revision:w.revision, piece
   })
   Object.assign(w,updated)
   message.value='工單 #'+w.id+' '+(pieces[piece] || '')+' 已回報 '+quantity
 } catch(e){message.value=e.message} finally{busy.value=false}
}
onMounted(load)
</script>
<template><main class="sheet worker-sheet"><header class="flex justify-between items-center"><h1 class="font-bold text-2xl">完工回報</h1><button @click="logout">登出</button></header>
<p>{{authState.username}} · 正式工單</p><button class="touch-target underline" @click="load">重新載入</button><p role="status">{{message}}</p>
<p v-if="!orders.length">目前沒有工單可顯示</p>
<article class="worker-card" v-for="w in orders" :key="w.id">
<b>#{{w.id}}　{{w.item_name}}</b><p>{{w.client}} · {{w.date}} · 工單數量 {{w.quantity}}</p>
<details class="paper-fold"><summary>廠內作業資料</summary>
<p v-for="(label,key) in shopFields" :key="key">{{label}}：{{w[key] || '未填'}}</p>
<p>正面 {{w.front_side ?? '—'}} 色 · 反面 {{w.back_side ?? '—'}} 色</p><p class="whitespace-pre-line">{{w.notes}}</p></details>
<CombinedOrder v-if="w.combined" :spec="w.combined" :reports="w.piece_reports" v-slot="{piece,label}">
  <form @submit.prevent="save(w,piece)">
    <label class="key-field report-quantity">{{label}}完成數量
      <input class="border p-2" type="number" inputmode="numeric" required min="0" max="2147483647" step="1" v-model="draft[w.id+'-'+piece]">
    </label>
    <button class="new-order" :disabled="busy">儲存{{label}}回報</button>
  </form>
</CombinedOrder>
<form v-else @submit.prevent="save(w)">
<label class="key-field report-quantity">完成數量 <input class="border p-2 w-32" type="number" inputmode="numeric" min="0" max="2147483647" step="1" required placeholder="尚未填報" v-model="draft[w.id]"></label>
<button class="new-order" :disabled="busy">儲存回報</button></form></article></main></template>
