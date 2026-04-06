<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { initializeSetup } from '../api/setup'

const router = useRouter()
const step = ref(1)
const loading = ref(false)
const error = ref('')

const form = reactive({
  company_name: '',
  admin_username: '',
  admin_email: '',
  admin_password: '',
  admin_password_confirm: '',
  router_name: '',
  router_url: '',
  router_username: 'admin',
  router_password: '',
})

function nextStep() {
  error.value = ''
  if (step.value === 1) {
    if (!form.company_name.trim()) { error.value = 'Company name is required'; return }
    step.value = 2
  } else if (step.value === 2) {
    if (!form.admin_username.trim()) { error.value = 'Username is required'; return }
    if (!form.admin_email.trim()) { error.value = 'Email is required'; return }
    if (!form.admin_password || form.admin_password.length < 6) { error.value = 'Password must be at least 6 characters'; return }
    if (form.admin_password !== form.admin_password_confirm) { error.value = 'Passwords do not match'; return }
    step.value = 3
  }
}

function prevStep() {
  error.value = ''
  if (step.value > 1) step.value--
}

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await initializeSetup({
      company_name: form.company_name,
      admin_username: form.admin_username,
      admin_email: form.admin_email,
      admin_password: form.admin_password,
      router_name: form.router_name || undefined,
      router_url: form.router_url || undefined,
      router_username: form.router_username || undefined,
      router_password: form.router_password || undefined,
    })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Setup failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-[#1a1a2e] to-sidebar px-4">
    <div class="absolute inset-0 opacity-5">
      <div class="absolute inset-0" style="background-image: radial-gradient(circle at 25% 25%, white 1px, transparent 1px); background-size: 50px 50px;" />
    </div>

    <div class="relative w-full max-w-lg">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white/10 backdrop-blur-sm mb-4">
          <img src="/logo-2.png" alt="NetLedger" class="w-16 h-16 object-contain" />
        </div>
        <h1 class="text-3xl font-bold text-white tracking-tight">NetLedger Setup</h1>
        <p class="text-gray-400 mt-1 text-sm">Let's get your ISP billing system ready</p>
      </div>

      <!-- Progress steps -->
      <div class="flex items-center justify-center gap-2 mb-6">
        <div v-for="s in 3" :key="s" class="flex items-center gap-2">
          <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors', s <= step ? 'bg-primary text-white' : 'bg-white/10 text-gray-400']">{{ s }}</div>
          <div v-if="s < 3" :class="['w-8 h-0.5', s < step ? 'bg-primary' : 'bg-white/10']" />
        </div>
      </div>

      <!-- Card -->
      <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-8">
        <div v-if="error" class="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">{{ error }}</div>

        <!-- Step 1: Company -->
        <div v-if="step === 1">
          <h2 class="text-lg font-semibold text-gray-900 mb-1">Company Information</h2>
          <p class="text-sm text-gray-500 mb-6">This will be used for branding your ISP portal.</p>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Company / ISP Name</label>
            <input v-model="form.company_name" type="text" placeholder="e.g. MyISP Internet Services" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" @keyup.enter="nextStep" />
          </div>
        </div>

        <!-- Step 2: Admin Account -->
        <div v-if="step === 2">
          <h2 class="text-lg font-semibold text-gray-900 mb-1">Admin Account</h2>
          <p class="text-sm text-gray-500 mb-6">Create your administrator login.</p>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">Username</label>
              <input v-model="form.admin_username" type="text" placeholder="admin" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
              <input v-model="form.admin_email" type="email" placeholder="admin@myisp.com" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
              <input v-model="form.admin_password" type="password" placeholder="Min. 6 characters" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">Confirm Password</label>
              <input v-model="form.admin_password_confirm" type="password" placeholder="Re-enter password" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" @keyup.enter="nextStep" />
            </div>
          </div>
        </div>

        <!-- Step 3: Router (optional) -->
        <div v-if="step === 3">
          <h2 class="text-lg font-semibold text-gray-900 mb-1">Connect Your Router</h2>
          <p class="text-sm text-gray-500 mb-6">Optional — you can add routers later from the Routers page.</p>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">Router Name</label>
              <input v-model="form.router_name" type="text" placeholder="e.g. Main Router" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">Router IP / URL</label>
              <input v-model="form.router_url" type="text" placeholder="e.g. 192.168.88.1" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">Username</label>
                <input v-model="form.router_username" type="text" placeholder="admin" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
                <input v-model="form.router_password" type="password" placeholder="Router password" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
              </div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-between mt-8">
          <button v-if="step > 1" @click="prevStep" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Back</button>
          <div v-else />
          <div class="flex gap-3">
            <button v-if="step === 3" @click="handleSubmit" :disabled="loading" class="px-6 py-2.5 rounded-lg bg-primary text-white font-medium text-sm hover:bg-primary-hover disabled:opacity-60 transition-colors">
              {{ loading ? 'Setting up...' : (form.router_name ? 'Complete Setup' : 'Skip & Finish') }}
            </button>
            <button v-else @click="nextStep" class="px-6 py-2.5 rounded-lg bg-primary text-white font-medium text-sm hover:bg-primary-hover transition-colors">Next</button>
          </div>
        </div>
      </div>

      <p class="text-center text-gray-500 text-xs mt-6">&copy; {{ new Date().getFullYear() }} NetLedger &mdash; 2max Tech</p>
    </div>
  </div>
</template>
