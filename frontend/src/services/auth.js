import { reactive } from 'vue'

export const authState = reactive({
  ready: false,
  authenticated: false,
  csrfToken: '',
})

const readError = async (response, fallback) => {
  try {
    const body = await response.json()
    return body.detail || fallback
  } catch {
    return fallback
  }
}

export const markLoggedOut = () => {
  authState.authenticated = false
  authState.csrfToken = ''
  authState.ready = true
}

export const initializeAuth = async () => {
  try {
    const response = await fetch('/api/auth/me', {
      credentials: 'same-origin',
      cache: 'no-store',
      headers: { 'ngrok-skip-browser-warning': 'true' },
    })
    if (!response.ok) {
      markLoggedOut()
      return
    }
    const body = await response.json()
    authState.authenticated = true
    authState.csrfToken = body.csrf_token
  } catch {
    markLoggedOut()
  } finally {
    authState.ready = true
  }
}

export const login = async (password) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
    body: JSON.stringify({ password }),
  })
  if (!response.ok) throw new Error(await readError(response, '登入失敗'))
  const body = await response.json()
  authState.authenticated = true
  authState.csrfToken = body.csrf_token
  authState.ready = true
}

export const logout = async () => {
  const response = await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { 'X-CSRF-Token': authState.csrfToken, 'ngrok-skip-browser-warning': 'true' },
  })
  if (!response.ok && response.status !== 401) {
    throw new Error(await readError(response, '登出失敗，請再試一次'))
  }
  markLoggedOut()
}
