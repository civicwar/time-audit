import axios from 'axios'

const STORAGE_KEY = 'timeAuditSession'

export const getStoredSession = () => {
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw)
  } catch {
    window.localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export const saveSession = (session) => {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

export const clearSession = () => {
  window.localStorage.removeItem(STORAGE_KEY)
}

const api = axios.create()

api.interceptors.request.use((config) => {
  const session = getStoredSession()
  if (session?.token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${session.token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearSession()
      if (window.location.pathname.startsWith('/in')) {
        window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default api