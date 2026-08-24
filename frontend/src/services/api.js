import axios from 'axios'

const api = axios.create({
  baseURL: '/api',  // 使用相對路徑，透過 Vite Proxy 轉發
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',  // 防止 Ngrok 攔截背景 API 請求
  },
})

// Request interceptor for loading state
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api