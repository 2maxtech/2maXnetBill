<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const token = route.params.token as string

const invoice = ref<any>(null)
const loading = ref(true)
const error = ref('')
const checkoutLoading = ref(false)

// Check for status query param (redirect from PayMongo)
const paymentStatus = computed(() => route.query.status as string | undefined)

const totalAmount = computed(() => {
  if (!invoice.value) return 0
  return Number(invoice.value.total_amount || invoice.value.amount || 0)
})

const baseAmount = computed(() => {
  if (!invoice.value) return 0
  return Number(invoice.value.amount || 0)
})

const feeAmount = computed(() => {
  if (!invoice.value) return 0
  return Number(invoice.value.convenience_fee || 0)
})

const hasFee = computed(() => feeAmount.value > 0)

function formatCurrency(val: number) {
  return '\u20B1' + val.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

onMounted(async () => {
  try {
    const response = await fetch(`/api/v1/pay/${token}`)
    if (!response.ok) {
      const data = await response.json()
      error.value = data.detail || 'Invoice not found'
      return
    }
    invoice.value = await response.json()
  } catch {
    error.value = 'Failed to load invoice'
  } finally {
    loading.value = false
  }
})

async function checkout() {
  checkoutLoading.value = true
  error.value = ''
  try {
    const response = await fetch(`/api/v1/pay/${token}/checkout`, { method: 'POST' })
    const data = await response.json()
    if (data.checkout_url) {
      window.location.href = data.checkout_url
    } else {
      error.value = data.detail || 'Failed to create checkout session'
    }
  } catch {
    error.value = 'Payment service unavailable'
  } finally {
    checkoutLoading.value = false
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
          <div class="h-5 w-40 bg-gray-100 rounded animate-pulse mb-2" />
          <div class="h-4 w-32 bg-gray-100 rounded animate-pulse mb-6" />
          <div class="w-full space-y-3">
            <div class="h-4 w-full bg-gray-100 rounded animate-pulse" />
            <div class="h-4 w-3/4 bg-gray-100 rounded animate-pulse" />
            <div class="h-12 w-full bg-gray-100 rounded-xl animate-pulse mt-4" />
          </div>
        </div>
      </div>
    </div>

    <!-- Payment Success -->
    <div v-else-if="paymentStatus === 'success'" class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-6">
          <svg class="w-10 h-10 text-green-600" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
        <p class="text-gray-500 mb-6">Your payment has been received. Your account will be updated shortly.</p>
        <div class="rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700">
          A confirmation receipt has been sent to your email/phone.
        </div>
      </div>
      <p class="text-center text-gray-400 text-xs mt-6">
        Powered by <span class="text-gray-500">NetLedger</span>
      </p>
    </div>

    <!-- Payment Cancelled -->
    <div v-else-if="paymentStatus === 'cancel'" class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 mb-6">
          <svg class="w-10 h-10 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Payment Cancelled</h1>
        <p class="text-gray-500 mb-6">Your payment was not completed. No charges were made.</p>
        <button
          @click="$router.replace({ query: {} })"
          class="w-full py-3 px-4 rounded-xl bg-primary text-white font-semibold text-sm hover:bg-primary-hover transition-colors"
        >
          Try Again
        </button>
      </div>
      <p class="text-center text-gray-400 text-xs mt-6">
        Powered by <span class="text-gray-500">NetLedger</span>
      </p>
    </div>

    <!-- Error -->
    <div v-else-if="error && !invoice" class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-red-100 mb-6">
          <svg class="w-10 h-10 text-red-500" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </div>
        <h1 class="text-xl font-bold text-gray-900 mb-2">Unable to Load Invoice</h1>
        <p class="text-gray-500">{{ error }}</p>
      </div>
      <p class="text-center text-gray-400 text-xs mt-6">
        Powered by <span class="text-gray-500">NetLedger</span>
      </p>
    </div>

    <!-- Invoice Payment -->
    <div v-else-if="invoice" class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <!-- Header with branding -->
        <div class="px-8 pt-8 pb-6 text-center">
          <div v-if="invoice.company_logo_url" class="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-gray-50 mb-3">
            <img :src="invoice.company_logo_url" :alt="invoice.company_name" class="max-w-[56px] max-h-[56px] object-contain" />
          </div>
          <h1 class="text-lg font-bold text-gray-900">{{ invoice.company_name || 'Invoice Payment' }}</h1>
        </div>

        <!-- Invoice details -->
        <div class="px-8 pb-6">
          <!-- Already paid -->
          <div v-if="invoice.status === 'paid'" class="text-center py-4">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
              <svg class="w-8 h-8 text-green-600" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </div>
            <h2 class="text-lg font-semibold text-green-700 mb-1">This invoice has been paid</h2>
            <p class="text-sm text-gray-500">No further action needed. Thank you!</p>
          </div>

          <!-- Unpaid invoice -->
          <template v-else>
            <div class="rounded-xl bg-gray-50 border border-gray-200 p-4 mb-5 space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-500">Customer</span>
                <span class="text-sm font-medium text-gray-900">{{ invoice.customer_name }}</span>
              </div>
              <div v-if="invoice.plan_name" class="flex justify-between items-center">
                <span class="text-sm text-gray-500">Plan</span>
                <span class="text-sm font-medium text-gray-900">{{ invoice.plan_name }}</span>
              </div>
              <div v-if="invoice.due_date" class="flex justify-between items-center">
                <span class="text-sm text-gray-500">Due Date</span>
                <span class="text-sm font-medium text-gray-900">{{ invoice.due_date }}</span>
              </div>

              <!-- Amount breakdown -->
              <div class="border-t border-gray-200 pt-3">
                <template v-if="hasFee">
                  <div class="flex justify-between items-center mb-1">
                    <span class="text-sm text-gray-500">Invoice</span>
                    <span class="text-sm text-gray-700">{{ formatCurrency(baseAmount) }}</span>
                  </div>
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-sm text-gray-500">Convenience fee</span>
                    <span class="text-sm text-gray-700">{{ formatCurrency(feeAmount) }}</span>
                  </div>
                  <div class="flex justify-between items-center pt-2 border-t border-gray-200">
                    <span class="text-sm font-semibold text-gray-900">Total</span>
                    <span class="text-xl font-bold text-gray-900">{{ formatCurrency(totalAmount) }}</span>
                  </div>
                </template>
                <template v-else>
                  <div class="flex justify-between items-center">
                    <span class="text-sm font-semibold text-gray-900">Amount</span>
                    <span class="text-xl font-bold text-gray-900">{{ formatCurrency(baseAmount) }}</span>
                  </div>
                </template>
              </div>
            </div>

            <!-- Error -->
            <div
              v-if="error"
              class="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700"
            >
              {{ error }}
            </div>

            <!-- Pay Now button -->
            <button
              @click="checkout"
              :disabled="checkoutLoading"
              class="w-full py-3.5 px-4 rounded-xl bg-primary text-white font-semibold text-base hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-60 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              <svg
                v-if="checkoutLoading"
                class="w-5 h-5 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ checkoutLoading ? 'Redirecting to payment...' : 'Pay Now' }}
            </button>

            <!-- Payment methods -->
            <div class="mt-4 flex items-center justify-center gap-3 text-xs text-gray-400">
              <span class="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-50 border border-gray-200 text-gray-500 font-medium">GCash</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-50 border border-gray-200 text-gray-500 font-medium">Maya</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-50 border border-gray-200 text-gray-500 font-medium">Visa / Mastercard</span>
            </div>
          </template>
        </div>
      </div>

      <!-- Footer -->
      <p class="text-center text-gray-400 text-xs mt-6">
        Secured by PayMongo &middot; Powered by <span class="text-gray-500">NetLedger</span>
      </p>
    </div>
  </div>
</template>
