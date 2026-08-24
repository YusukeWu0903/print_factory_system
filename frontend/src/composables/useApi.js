import { ref, computed } from 'vue'
import api from '@/services/api'

export function useClients() {
  const clients = ref([])
  const loading = ref(false)
  const error = ref(null)

  const fetchClients = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/clients/')
      clients.value = response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入客戶失敗'
    } finally {
      loading.value = false
    }
  }

  const createClient = async (data) => {
    const response = await api.post('/clients/', data)
    clients.value.unshift(response.data)
    return response.data
  }

  const updateClient = async (id, data) => {
    const response = await api.patch(`/clients/${id}`, data)
    const index = clients.value.findIndex(c => c.id === id)
    if (index !== -1) clients.value[index] = response.data
    return response.data
  }

  const deleteClient = async (id) => {
    await api.delete(`/clients/${id}`)
    clients.value = clients.value.filter(c => c.id !== id)
  }

  return { clients, loading, error, fetchClients, createClient, updateClient, deleteClient }
}

export function useWorkOrders() {
  const workOrders = ref([])
  const loading = ref(false)
  const error = ref(null)

  const fetchWorkOrders = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/work-orders/', { params })
      workOrders.value = response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入工單失敗'
    } finally {
      loading.value = false
    }
  }

  const createWorkOrder = async (data) => {
    const response = await api.post('/work-orders/', data)
    workOrders.value.unshift(response.data)
    return response.data
  }

  const updateWorkOrder = async (id, data) => {
    const response = await api.patch(`/work-orders/${id}`, data)
    const index = workOrders.value.findIndex(w => w.id === id)
    if (index !== -1) workOrders.value[index] = response.data
    return response.data
  }

  const updateWorkOrderStatus = async (id, status) => {
    const response = await api.patch(`/work-orders/${id}/status`, { status })
    const index = workOrders.value.findIndex(w => w.id === id)
    if (index !== -1) workOrders.value[index] = response.data
    return response.data
  }

  const deleteWorkOrder = async (id) => {
    await api.delete(`/work-orders/${id}`)
    workOrders.value = workOrders.value.filter(w => w.id !== id)
  }

  return { workOrders, loading, error, fetchWorkOrders, createWorkOrder, updateWorkOrder, updateWorkOrderStatus, deleteWorkOrder }
}

export function useStatusHelpers() {
  const statusColors = {
    '印製中': 'bg-blue-100 text-blue-800 border-blue-200',
    '已完成_待請款': 'bg-amber-100 text-amber-800 border-amber-200',
    '已請款': 'bg-green-100 text-green-800 border-green-200',
  }

  const statusLabels = {
    '印製中': '印製中',
    '已完成_待請款': '已完成·待請款',
    '已請款': '已請款',
  }

  const getStatusClass = (status) => statusColors[status] || 'bg-gray-100 text-gray-800 border-gray-200'
  const getStatusLabel = (status) => statusLabels[status] || status

  const nextStatus = (currentStatus) => {
    const transitions = {
      '印製中': '已完成_待請款',
      '已完成_待請款': '已請款',
    }
    return transitions[currentStatus]
  }

  return { statusColors, statusLabels, getStatusClass, getStatusLabel, nextStatus }
}