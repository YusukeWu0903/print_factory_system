<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import { authState, initializeAuth } from '@/services/auth'

onMounted(initializeAuth)
</script>

<template>
  <div v-if="!authState.ready" class="min-h-screen flex items-center justify-center bg-amber-50 text-amber-900">載入中…</div>
  <LoginView v-else-if="!authState.authenticated" />
  <RouterView v-else />
</template>

<style>
/* Global styles */
html {
  -webkit-text-size-adjust: 100%;
  -webkit-tap-highlight-color: transparent;
}

body {
  overscroll-behavior: none;
}

/* Focus visible for accessibility */
:focus-visible {
  outline: 2px solid #14b8a6;
  outline-offset: 2px;
}
</style>
