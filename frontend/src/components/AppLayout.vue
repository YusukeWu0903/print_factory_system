<script setup>
import {ref} from 'vue'
import StaffAccounts from './StaffAccounts.vue'
const manageStaff=ref(false)
import { useRouter, useRoute } from 'vue-router'
import { logout, authState } from '@/services/auth'
import { dataMode, switchDataMode } from '@/services/dataMode'

const router = useRouter()
const route = useRoute()

const props = defineProps({
  title: {
    type: String,
    default: '工單管理',
  },
  showBack: {
    type: Boolean,
    default: false,
  },
  fabAction: {
    type: Function,
    default: null,
  },
  fabLabel: {
    type: String,
    default: '新增工單',
  },
})



const handleBack = () => {
  if (route.path !== '/') {
    router.back()
  }
}

const handleFAB = () => {
  if (props.fabAction) {
    props.fabAction()
  }
}

// Navigation items
const navItems = [
  { path: '/', label: '工單工作台', icon: 'list' },
  { path: '/reconciliation', label: '月底對帳', icon: 'calculator' },
  { path: '/clients', label: '客戶管理', icon: 'users' },
]

const handleLogout = async () => {
  try {
    await logout()
    router.push('/')
  } catch (err) {
    alert(err.message || '登出失敗，請再試一次')
  }
}

</script>
<template>
  <div class="press">
    <header class="mast"><div class="mast-inner">
      <router-link to="/" class="brand"><i aria-hidden="true"></i>印務帳本</router-link>
      <nav aria-label="主要導覽"><router-link v-for="item in navItems" :key="item.path" :to="item.path">{{ item.label }}</router-link></nav>
      <div class="account"><b>{{ dataMode === 'sandbox' ? '測試環境' : '正式環境' }}</b>
        <template v-if="!authState.publicSandbox"><button @click="switchDataMode">{{ dataMode === 'sandbox' ? '切回正式' : '進入測試' }}</button><button v-if="dataMode === 'production'" @click="manageStaff=!manageStaff">{{manageStaff ? '返回工單' : '員工帳號'}}</button><button @click="handleLogout">登出</button></template>
      </div>
    </div></header>
    <StaffAccounts v-if="manageStaff && !authState.publicSandbox && dataMode === 'production'" /><main v-else class="sheet">
      <div class="headline"><div><button v-if="showBack" @click="handleBack">← 返回</button><h1>{{ title }}</h1></div>
        <button v-if="fabAction" class="new-order" @click="handleFAB">＋ {{ fabLabel }}</button>
      </div>
      <slot />
    </main>
  </div>
</template>
