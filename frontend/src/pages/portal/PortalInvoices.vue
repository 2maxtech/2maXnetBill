<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import dayjs from 'dayjs'
import { getPortalInvoices, downloadPortalInvoicePdf, type PortalInvoice } from '../../api/portal'
import StatusBadge from '../../components/common/StatusBadge.vue'
import Pagination from '../../components/common/Pagination.vue'

const invoices = ref<PortalInvoice[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)

function formatCurrency(val: number | string) {
  return '\u20B1' + Number(val).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function fetchInvoices() {
  loading.value = true
  try {
    const { data } = await getPortalInvoices({ page: page.value, size: pageSize })
    invoices.value = data.items
    total.value = data.total
  } catch (e) {
    console.error('Failed to fetch invoices', e)
  } finally {
    loading.value = false
  }
}

function handlePrint(inv: PortalInvoice) {
  window.open(`/api/v1/portal/invoices/${inv.id}/pdf`, '_blank')
}

async function handleDownload(inv: PortalInvoice) {
  try {
    const { data } = await downloadPortalInvoicePdf(inv.id)
    const url = window.URL.createObjectURL(new Blob([data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `invoice-${inv.id}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('PDF download failed', e)
  }
}

watch(page, fetchInvoices)
onMounted(fetchInvoices)
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">My Invoices</h1>

    <!-- Table -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Plan</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Amount</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Paid</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Due Date</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Status</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Issued</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <!-- Loading -->
            <template v-if="loading">
              <tr v-for="i in 5" :key="i">
                <td v-for="j in 7" :key="j" class="px-4 py-3">
                  <div class="h-4 bg-gray-100 rounded animate-pulse" />
                </td>
              </tr>
            </template>
            <!-- Empty -->
            <tr v-else-if="!invoices.length">
              <td colspan="7" class="px-4 py-12 text-center text-gray-400">No invoices found</td>
            </tr>
            <!-- Rows -->
            <tr v-else v-for="inv in invoices" :key="inv.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-4 py-3 text-sm text-gray-700 font-medium">{{ inv.plan_name }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ formatCurrency(inv.amount) }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ formatCurrency(inv.total_paid) }}</td>
              <td class="px-4 py-3 text-sm text-gray-700">{{ dayjs(inv.due_date).format('MMM D, YYYY') }}</td>
              <td class="px-4 py-3"><StatusBadge :status="inv.status" /></td>
              <td class="px-4 py-3 text-sm text-gray-500">{{ dayjs(inv.issued_at).format('MMM D, YYYY') }}</td>
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-1">
                  <a
                    v-if="inv.payment_token && inv.status !== 'paid'"
                    :href="`/pay/${inv.payment_token}`"
                    class="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors"
                  >
                    Pay Now
                  </a>
                  <button
                    @click="handlePrint(inv)"
                    title="Print"
                    class="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                  >
                    <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5 4v3H4a2 2 0 00-2 2v3a2 2 0 002 2h1v2a2 2 0 002 2h6a2 2 0 002-2v-2h1a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z" clip-rule="evenodd" /></svg>
                  </button>
                  <button
                    @click="handleDownload(inv)"
                    title="Download PDF"
                    class="p-1.5 rounded-lg text-gray-400 hover:text-primary hover:bg-orange-50 transition-colors"
                  >
                    <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pagination
        :page="page"
        :page-size="pageSize"
        :total="total"
        @update:page="page = $event"
      />
    </div>
  </div>
</template>
