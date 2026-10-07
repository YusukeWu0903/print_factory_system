import { ref } from 'vue'

const STORAGE_KEY = 'print_factory_data_mode'
const savedMode = localStorage.getItem(STORAGE_KEY)

export const dataMode = ref(savedMode === 'sandbox' ? 'sandbox' : 'production')

export const switchDataMode = () => {
  const nextMode = dataMode.value === 'production' ? 'sandbox' : 'production'
  localStorage.setItem(STORAGE_KEY, nextMode)
  window.location.replace('/')
}
