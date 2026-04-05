import { ref, computed } from 'vue'
import { login as apiLogin, getMe, type User } from '../api/auth'

const user = ref<User | null>(null)
const isLoading = ref(true)

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value)

  async function init() {
    const token = localStorage.getItem('access_token')
    if (!token) {
      isLoading.value = false
      return
    }
    try {
      const { data } = await getMe()
      user.value = data
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      user.value = null
    } finally {
      isLoading.value = false
    }
  }

  async function login(username: string, password: string) {
    const { data } = await apiLogin(username, password)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    const me = await getMe()
    user.value = me.data
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
    window.location.href = '/login'
  }

  return { user, isAuthenticated, isLoading, init, login, logout }
}
