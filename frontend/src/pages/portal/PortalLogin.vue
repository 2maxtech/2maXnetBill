<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { portalLogin } from '../../api/portal'

const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  if (!email.value || !password.value) {
    error.value = 'Please enter both email and password.'
    return
  }
  loading.value = true
  try {
    const { data } = await portalLogin(email.value, password.value)
    localStorage.setItem('portal_token', data.access_token)
    localStorage.setItem('portal_customer', JSON.stringify(data.customer))
    router.push('/portal')
  } catch (e: any) {
    error.value =
      e.response?.data?.detail ||
      e.response?.data?.message ||
      'Invalid credentials. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-[#1a1a2e] to-sidebar px-4">
    <!-- Subtle background pattern -->
    <div class="absolute inset-0 opacity-5">
      <div class="absolute inset-0" style="background-image: radial-gradient(circle at 25% 25%, white 1px, transparent 1px); background-size: 50px 50px;" />
    </div>

    <div class="relative w-full max-w-md">
      <!-- Logo & Title -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white/10 backdrop-blur-sm mb-4">
          <img src="/logo-2.png" alt="NetLedger" class="w-16 h-16 object-contain" />
        </div>
        <h1 class="text-3xl font-bold text-white tracking-tight">Customer Portal</h1>
        <p class="text-gray-400 mt-1 text-sm">NetLedger &mdash; ISP Billing</p>
      </div>

      <!-- Login Card -->
      <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-8">
        <h2 class="text-lg font-semibold text-gray-900 mb-6">Sign in to your account</h2>

        <!-- Error Alert -->
        <div
          v-if="error"
          class="mb-4 flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700"
        >
          <svg class="w-5 h-5 shrink-0 mt-0.5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" />
          </svg>
          <span>{{ error }}</span>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-5">
          <!-- Email -->
          <div>
            <label for="portal-email" class="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="w-5 h-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                </svg>
              </div>
              <input
                id="portal-email"
                v-model="email"
                type="email"
                autocomplete="email"
                placeholder="Enter your email"
                class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
              />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label for="portal-password" class="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="w-5 h-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" clip-rule="evenodd" />
                </svg>
              </div>
              <input
                id="portal-password"
                v-model="password"
                type="password"
                autocomplete="current-password"
                placeholder="Enter your password"
                class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
              />
            </div>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-primary text-white font-medium text-sm hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            <svg
              v-if="loading"
              class="w-4 h-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ loading ? 'Signing in...' : 'Sign in' }}
          </button>
        </form>
      </div>

      <!-- Footer -->
      <p class="text-center text-gray-500 text-xs mt-6">
        &copy; {{ new Date().getFullYear() }} NetLedger &mdash; 2max Tech
      </p>
    </div>
  </div>
</template>
