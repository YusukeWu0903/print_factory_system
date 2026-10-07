import axios from 'axios'
import { authState, markLoggedOut } from './auth'
import { dataMode } from './dataMode'

const api = axios.create({
  baseURL: '/api',  // 使用相對路徑，透過 Vite Proxy 轉發
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',  // 防止 Ngrok 攔截背景 API 請求
  },
})

// Request interceptor for loading state
api.interceptors.request.use(
  (config) => {
    config.headers['X-Data-Mode'] = dataMode.value
    if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase()) && authState.csrfToken) {
      config.headers['X-CSRF-Token'] = authState.csrfToken
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    if (response.headers['x-data-mode'] !== dataMode.value) {
      throw new Error('資料環境驗證失敗，請重新整理頁面')
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401) markLoggedOut()
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api
