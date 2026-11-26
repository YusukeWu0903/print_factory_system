<script setup>
import {ref,onMounted} from 'vue'
import {staffRequest} from '@/services/staff'
const rows=ref([]),name=ref(''),password=ref(''),selected=ref(''),message=ref('')
async function load(){rows.value=await staffRequest('accounts')}
async function save(){
  try{
    if(selected.value) await staffRequest('accounts?username='+encodeURIComponent(selected.value),'PATCH',{password:password.value})
    else await staffRequest('accounts','POST',{username:name.value,password:password.value})
    password.value='';name.value='';selected.value='';await load();message.value='帳號已儲存'
  }catch(e){message.value=e.message}
}
async function toggle(e){
 if(!confirm('確定'+(e.active?'停用':'啟用')+'「'+e.username+'」？'))return
 try{await staffRequest('accounts?username='+encodeURIComponent(e.username),'PATCH',{active:!e.active});await load();message.value='帳號狀態已更新'}catch(err){message.value=err.message}
}
onMounted(()=>load().catch(e=>message.value=e.message))
</script>
<template><section class="sheet"><h1 class="text-2xl font-bold">員工帳號</h1>
<form @submit.prevent="save" class="space-y-3 py-4">
<label class="block">姓名或帳號 <input class="border p-2" required v-model.trim="name" maxlength="50" :disabled="!!selected"></label>
<label class="block">設定密碼 <input type="password" autocomplete="new-password" class="border p-2" required minlength="8" maxlength="128" placeholder="至少 8 字元" v-model="password"></label>
<button class="new-order">{{selected?'儲存新密碼':'新增師傅'}}</button>
<button type="button" v-if="selected" @click="selected='';name='';password=''">取消</button></form>
<p role="status">{{message}}</p>
<div v-for="e in rows" :key="e.username" class="flex flex-wrap items-center gap-4 border-t py-2"><b>{{e.username}}</b>{{e.active?'使用中':'已停用'}}
<button class="touch-target" @click="selected=e.username;name=e.username;password=''">重設密碼</button><button class="touch-target" @click="toggle(e)">{{e.active?'停用':'啟用'}}</button></div></section></template>
