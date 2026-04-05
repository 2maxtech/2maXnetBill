<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import { getPortalDashboard, type PortalDashboard } from '../../api/portal'
import StatusBadge from '../../components/common/StatusBadge.vue'

const dashboard = ref<PortalDashboard | null>(null)
const loading = ref(true)

function formatCurrency(val: number | string) {
  return '\u20B1' + Number(val).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i]
}

async function fetchDashboard() {
  loading.value = true
  try {
    const { data } = await getPortalDashboard()
    dashboard.value = data
  } catch (e) {
    console.error('Failed to load portal dashboard', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboard)
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">My Account</h1>

    <!-- Loading -->
    <div v-if="loading" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div v-for="i in 3" :key="i" class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
          <div class="h-4 w-24 bg-gray-100 rounded animate-pulse mb-3" />
          <div class="h-6 w-32 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    </div>

    <template v-else-if="dashboard">
      <!-- Top Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Account Status -->
        <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
          <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Account Status</p>
          <StatusBadge :status="dashboard.status" />
        </div>

        <!-- Plan Info -->
        <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
          <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Current Plan</p>
          <p class="text-lg font-bold text-gray-900">{{ dashboard.plan.name }}</p>
          <p class="text-sm text-gray-500 mt-1">
            {{ dashboard.plan.download_mbps }} Mbps / {{ dashboard.plan.upload_mbps }} Mbps
          </p>
          <p class="text-sm font-semibold text-primary mt-1">{{ formatCurrency(dashboard.plan.monthly_price) }}/mo</p>
        </div>

        <!-- Outstanding Balance -->
        <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
          <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Outstanding Balance</p>
          <p :class="[
            'text-2xl font-bold',
            dashboard.outstanding_balance > 0 ? 'text-red-600' : 'text-green-600'
          ]">
            {{ formatCurrency(dashboard.outstanding_balance) }}
          </p>
        </div>
      </div>

      <!-- Active Session -->
      <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">Active Session</h2>
        <template v-if="dashboard.session">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p class="text-xs font-medium text-gray-500 uppercase">IP Address</p>
              <p class="text-sm font-medium text-gray-900 mt-1">{{ dashboard.session.address }}</p>
            </div>
            <div>
              <p class="text-xs font-medium text-gray-500 uppercase">Uptime</p>
              <p class="text-sm font-medium text-gray-900 mt-1">{{ dashboard.session.uptime }}</p>
            </div>
            <div>
              <p class="text-xs font-medium text-gray-500 uppercase">Data In</p>
              <p class="text-sm font-medium text-gray-900 mt-1">{{ formatBytes(dashboard.session.bytes_in) }}</p>
            </div>
            <div>
              <p class="text-xs font-medium text-gray-500 uppercase">Data Out</p>
              <p class="text-sm font-medium text-gray-900 mt-1">{{ formatBytes(dashboard.session.bytes_out) }}</p>
            </div>
          </div>
        </template>
        <div v-else class="text-center py-6">
          <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gray-100 mb-3">
            <svg class="w-6 h-6 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
          <p class="text-sm text-gray-500">No active session</p>
        </div>
      </div>

      <!-- Recent Invoices -->
      <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h2 class="text-lg font-semibold text-gray-800">Recent Invoices</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-100">
                <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Amount</th>
                <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Due Date</th>
                <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-if="!dashboard.recent_invoices?.length">
                <td colspan="3" class="px-4 py-8 text-center text-gray-400">No invoices yet</td>
              </tr>
              <tr v-else v-for="inv in dashboard.recent_invoices" :key="inv.id" class="hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-3 text-sm text-gray-700 text-right font-medium">{{ formatCurrency(inv.amount) }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ dayjs(inv.due_date).format('MMM D, YYYY') }}</td>
                <td class="px-4 py-3"><StatusBadge :status="inv.status" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
