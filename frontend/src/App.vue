<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView />
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