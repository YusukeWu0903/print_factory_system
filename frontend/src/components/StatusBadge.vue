<script setup>
import { useStatusHelpers } from '@/composables/useApi'

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
  clickable: {
    type: Boolean,
    default: false,
  },
})

const emits = defineEmits(['click'])

// Call the composable to get the helper functions
const { getStatusClass, getStatusLabel } = useStatusHelpers()

const statusClass = getStatusClass(props.status)
const statusLabel = getStatusLabel(props.status)

const handleClick = () => {
  if (props.clickable) {
    emits('click', props.status)
  }
}
</script>

<template>
  <span
    :class="[
      'inline-flex items-center px-2.5 py-1 rounded-full text-sm font-medium border',
      statusClass,
      { 'cursor-pointer active:scale-[0.98] transition-transform': clickable }
    ]"
    @click="handleClick"
    :aria-label="`工單狀態：${statusLabel}`"
  >
    {{ statusLabel }}
  </span>
</template>

<style scoped>
/* Status badge animations */
span {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
</style>