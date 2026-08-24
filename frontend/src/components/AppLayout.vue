<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

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

const fabVisible = ref(true)

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
  { path: '/', label: '工單列表', icon: 'list' },
  { path: '/reconciliation', label: '月底對帳', icon: 'calculator' },
]

// Hide FAB on scroll down, show on scroll up
let lastScrollY = 0
const handleScroll = () => {
  const currentScrollY = window.scrollY
  if (currentScrollY > lastScrollY && currentScrollY > 100) {
    fabVisible.value = false
  } else {
    fabVisible.value = true
  }
  lastScrollY = currentScrollY
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-amber-50 via-orange-50 to-amber-100 flex flex-col">
    <!-- Top Navigation Bar - Warm amber gradient -->
    <header class="sticky top-0 z-40 bg-gradient-to-r from-amber-100 to-orange-100 border-b border-amber-200 shadow-sm">
      <div class="flex items-center h-14 px-4 gap-3">
        <!-- Back Button / Menu -->
        <button
          v-if="showBack"
          @click="handleBack"
          class="touch-target flex items-center justify-center text-amber-700 hover:text-amber-900 hover:bg-amber-200 rounded-lg transition-colors -ml-1"
          aria-label="返回"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div v-else class="w-10" />

        <!-- Title -->
        <h1 class="flex-1 text-center text-lg font-semibold text-amber-900 truncate">
          {{ title }}
        </h1>

        <!-- Spacer for centering -->
        <div class="w-10" />
      </div>

      <!-- Navigation Tabs -->
      <nav class="flex border-t border-amber-200 bg-white/50 px-2 py-1" role="tablist" aria-label="主要導航">
        <button
          v-for="item in navItems"
          :key="item.path"
          :class="[
            'touch-target px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
            route.path === item.path
              ? 'bg-amber-100 text-amber-700'
              : 'text-gray-600 hover:bg-amber-50'
          ]"
          @click="router.push(item.path)"
          role="tab"
          :aria-selected="route.path === item.path"
        >
          {{ item.label }}
        </button>
      </nav>
    </header>

    <!-- Main Content - with proper top padding to avoid header overlap -->
    <main class="flex-1 overflow-y-auto pb-28 pt-2">
      <slot />
    </main>

    <!-- Floating Action Button (FAB) - Warm amber gradient -->
    <div
      v-if="fabAction"
      :class="[
        'fixed bottom-6 right-4 z-30 transition-all duration-200',
        { 'opacity-100 scale-100': fabVisible, 'opacity-0 scale-90 pointer-events-none': !fabVisible }
      ]"
    >
      <button
        @click="handleFAB"
        class="touch-target w-14 h-14 rounded-full bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-lg hover:from-amber-600 hover:to-orange-600 active:scale-95 transition-all flex items-center justify-center"
        :aria-label="fabLabel"
      >
        <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Safe area for notched devices */
@supports (padding: max(0px)) {
  header {
    padding-top: max(0px, env(safe-area-inset-top));
  }
  main {
    padding-bottom: max(112px, env(safe-area-inset-bottom) + 112px);
  }
}

/* Warm scrollbar for the whole app */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: #fef3e2;
}
::-webkit-scrollbar-thumb {
  background: #fbbf24;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #f59e0b;
}
</style>