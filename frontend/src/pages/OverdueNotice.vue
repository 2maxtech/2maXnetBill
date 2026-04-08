<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const slug = computed(() => route.params.slug as string | undefined)

const tenant = ref<any>(null)
const loading = ref(true)
const error = ref('')

// Username lookup (generic mode)
const username = ref('')
const lookupLoading = ref(false)
const lookupError = ref('')

onMounted(async () => {
  if (slug.value) {
    // Tenant-specific mode
    try {
      const response = await fetch(`/api/v1/notice/${slug.value}`)
      if (!response.ok) {
        error.value = 'Unable to load page'
        return
      }
      tenant.value = await response.json()
    } catch {
      error.value = 'Unable to load page'
    } finally {
      loading.value = false
    }
  } else {
    // Generic mode — show username lookup
    loading.value = false
  }
})

async function lookupPortal() {
  if (!username.value.trim()) return
  lookupLoading.value = true
  lookupError.value = ''
  try {
    const response = await fetch('/api/v1/notice/lookup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value.trim() }),
    })
    if (!response.ok) {
      const data = await response.json()
      lookupError.value = data.detail || 'Account not found'
      return
    }
    tenant.value = await response.json()
  } catch {
    lookupError.value = 'Service unavailable. Please try again.'
  } finally {
    lookupLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-100 flex items-center justify-center px-4 py-8">
    <!-- Loading -->
    <div v-if="loading" class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
        <div class="flex flex-col items-center">
          <div class="w-16 h-16 rounded-full bg-gray-100 animate-pulse mb-4" />
          <div class="h-5 w-48 bg-gray-100 rounded animate-pulse mb-2" />
          <div class="h-4 w-36 bg-gray-100 rounded animate-pulse mb-6" />
          <div class="w-full space-y-3">
            <div class="h-4 w-full bg-gray-100 rounded animate-pulse" />
            <div class="h-4 w-3/4 bg-gray-100 rounded animate-pulse" />
            <div class="h-12 w-full bg-gray-100 rounded-xl animate-pulse mt-4" />
          </div>
        </div>
      </div>
    </div>

    <!-- Error (only for slug mode) -->
    <div v-else-if="error && slug" class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-red-100 mb-6">
          <svg class="w-10 h-10 text-red-500" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </div>
        <h1 class="text-xl font-bold text-gray-900 mb-2">Page Not Available</h1>
        <p class="text-gray-500">{{ error }}</p>
      </div>
    </div>

    <!-- Generic mode: username lookup (no slug, no tenant yet) -->
    <div v-else-if="!tenant" class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <div class="px-8 pt-8 pb-4 text-center">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-amber-100 mb-5">
            <svg class="w-10 h-10 text-amber-600" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
          <h1 class="text-xl font-bold text-gray-900 mb-2">Internet Service Limited</h1>
          <p class="text-gray-600 text-sm leading-relaxed mb-6">
            Your internet service has been restricted due to an unpaid balance.
            Enter your PPPoE username below to find your payment portal.
          </p>
        </div>

        <div class="px-8 pb-8">
          <form @submit.prevent="lookupPortal" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">PPPoE Username</label>
              <input
                v-model="username"
                type="text"
                placeholder="Enter your PPPoE username"
                class="w-full px-4 py-3 rounded-xl border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500 transition-colors"
                :disabled="lookupLoading"
              />
            </div>

            <div v-if="lookupError" class="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {{ lookupError }}
            </div>

            <button
              type="submit"
              :disabled="lookupLoading || !username.trim()"
              class="w-full py-3.5 px-4 rounded-xl bg-amber-500 text-white font-semibold text-base hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              <svg v-if="lookupLoading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ lookupLoading ? 'Looking up...' : 'Find My Portal' }}
            </button>
          </form>
        </div>
      </div>

      <p class="text-center text-gray-400 text-xs mt-6">
        Powered by <span class="text-gray-500">NetLedger</span>
      </p>
    </div>

    <!-- Tenant-specific overdue notice (slug mode or after lookup) -->
    <div v-else class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <!-- Header with branding -->
        <div class="px-8 pt-8 pb-4 text-center">
          <div v-if="tenant.company_logo_url" class="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-gray-50 mb-3">
            <img :src="tenant.company_logo_url" :alt="tenant.company_name" class="max-w-[56px] max-h-[56px] object-contain" />
          </div>
          <h1 class="text-lg font-bold text-gray-900">{{ tenant.company_name }}</h1>
        </div>

        <!-- Warning icon + message -->
        <div class="px-8 pb-8">
          <div class="flex flex-col items-center text-center mb-6">
            <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-amber-100 mb-5">
              <svg class="w-10 h-10 text-amber-600" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
            </div>
            <h2 class="text-xl font-bold text-gray-900 mb-2">Internet Service Limited</h2>
            <p class="text-gray-600 text-sm leading-relaxed">
              Your internet service has been restricted due to an unpaid balance.
              Please pay your outstanding invoice to restore full speed.
            </p>
          </div>

          <!-- Steps -->
          <div class="rounded-xl bg-gray-50 border border-gray-200 p-4 mb-6 space-y-3">
            <h3 class="text-sm font-semibold text-gray-700 mb-2">How to restore your service:</h3>
            <div class="flex items-start gap-3">
              <span class="flex-shrink-0 w-6 h-6 rounded-full bg-amber-100 text-amber-700 text-xs font-bold flex items-center justify-center">1</span>
              <p class="text-sm text-gray-600">Log in to your Customer Portal using your PPPoE username and password</p>
            </div>
            <div class="flex items-start gap-3">
              <span class="flex-shrink-0 w-6 h-6 rounded-full bg-amber-100 text-amber-700 text-xs font-bold flex items-center justify-center">2</span>
              <p class="text-sm text-gray-600">View your unpaid invoices and click "Pay Now"</p>
            </div>
            <div class="flex items-start gap-3">
              <span class="flex-shrink-0 w-6 h-6 rounded-full bg-amber-100 text-amber-700 text-xs font-bold flex items-center justify-center">3</span>
              <p class="text-sm text-gray-600">Pay via GCash, Maya, or Visa/Mastercard</p>
            </div>
            <div class="flex items-start gap-3">
              <span class="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-bold flex items-center justify-center">
                <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
              </span>
              <p class="text-sm text-gray-600">Your full speed will be restored automatically after payment</p>
            </div>
          </div>

          <!-- CTA button -->
          <a
            :href="tenant.portal_url"
            class="block w-full py-3.5 px-4 rounded-xl text-white font-semibold text-base text-center transition-colors"
            :style="{ backgroundColor: tenant.primary_color || '#e8700a' }"
          >
            Go to Customer Portal
          </a>

          <!-- Payment methods -->
          <div class="mt-4 flex items-center justify-center gap-3 text-xs text-gray-400">
            <span class="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-50 border border-gray-200 text-gray-500 font-medium">GCash</span>
            <span class="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-50 border border-gray-200 text-gray-500 font-medium">Maya</span>
            <span class="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-50 border border-gray-200 text-gray-500 font-medium">Visa / MC</span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <p class="text-center text-gray-400 text-xs mt-6">
        Powered by <span class="text-gray-500">NetLedger</span>
      </p>
    </div>
  </div>
</template>
