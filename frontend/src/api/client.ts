import axios from 'axios'

let _tenantId: string | null = null

export function setTenantId(id: string | null) {
  _tenantId = id
}

const api = axios.create({
  baseURL: '/api/v1',
})

let isRefreshing = false
let failedQueue: Array<{ resolve: (v: any) => void; reject: (e: any) => void }> = []

function processQueue(error: any, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token)
  })
  failedQueue = []
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (_tenantId) {
    config.headers['X-Tenant-Id'] = _tenantId
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }
      originalRequest._retry = true
      isRefreshing = true
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) throw new Error('No refresh token')
        const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        api.defaults.headers.common.Authorization = `Bearer ${data.access_token}`
        processQueue(null, data.access_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return api(originalRequest)
      } catch (e) {
        processQueue(e, null)
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(e)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)

export default api

// Portal API client
export const portalApi = axios.create({
  baseURL: '/api/v1/portal',
})

portalApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('portal_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

portalApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('portal_token')
      localStorage.removeItem('portal_customer')
      window.location.href = '/portal/login'
    }
    return Promise.reject(error)
  }
)
