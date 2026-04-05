<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import Modal from '../components/common/Modal.vue'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import Pagination from '../components/common/Pagination.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import {
  getVouchers,
  generateVouchers,
  redeemVoucher,
  revokeVoucher,
  type VoucherType,
} from '../api/vouchers'
import { getPlans, type Plan } from '../api/plans'
import { getCustomers, type Customer } from '../api/customers'

const vouchers = ref<VoucherType[]>([])
const plans = ref<Plan[]>([])
const customers = ref<Customer[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)

const filterStatus = ref('')
const STATUSES = ['unused', 'active', 'expired', 'revoked']

// Generate modal
const showGenerateModal = ref(false)
const generating = ref(false)
const generateForm = ref({ plan_id: '', count: 10, duration_days: 30 })
const generatedCodes = ref<string[]>([])
const showCodesModal = ref(false)

// Redeem modal
const showRedeemModal = ref(false)
const redeeming = ref(false)
const redeemForm = ref({ code: '', customer_id: '' })
const redeemError = ref('')
const customerSearch = ref('')

// Revoke confirm
const confirmRevoke = ref(false)
const revokingId = ref('')
const revoking = ref(false)

// Clipboard feedback
const copiedCode = ref('')

async function loadVouchers() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, size: pageSize }
    if (filterStatus.value) params.status = filterStatus.value
    const { data } = await getVouchers(params)
    if (Array.isArray(data)) {
      vouchers.value = data
      total.value = data.length
    } else {
      vouchers.value = data.items
      total.value = data.total
    }
  } catch (e) {
    console.error('Failed to load vouchers', e)
  } finally {
    loading.value = false
  }
}

async function loadPlans() {
  try {
    const { data } = await getPlans({ active_only: true })
    plans.value = data
  } catch (e) {
    console.error('Failed to load plans', e)
  }
}

async function loadCustomers() {
  try {
    const { data } = await getCustomers({ page_size: 500 })
    customers.value = data.items
  } catch (e) {
    console.error('Failed to load customers', e)
  }
}

function openGenerate() {
  generateForm.value = { plan_id: plans.value[0]?.id || '', count: 10, duration_days: 30 }
  showGenerateModal.value = true
}

async function doGenerate() {
  generating.value = true
  try {
    const { data } = await generateVouchers({
      plan_id: generateForm.value.plan_id,
      count: generateForm.value.count,
      duration_days: generateForm.value.duration_days,
    })
    generatedCodes.value = data.map((v: VoucherType) => v.code)
    showGenerateModal.value = false
    showCodesModal.value = true
    await loadVouchers()
  } catch (e) {
    console.error('Failed to generate vouchers', e)
  } finally {
    generating.value = false
  }
}

function openRedeem() {
  redeemForm.value = { code: '', customer_id: '' }
  redeemError.value = ''
  customerSearch.value = ''
  showRedeemModal.value = true
}

async function doRedeem() {
  redeeming.value = true
  redeemError.value = ''
  try {
    await redeemVoucher({
      code: redeemForm.value.code,
      customer_id: redeemForm.value.customer_id,
    })
    showRedeemModal.value = false
    await loadVouchers()
  } catch (e: any) {
    redeemError.value = e.response?.data?.detail || 'Failed to redeem voucher.'
  } finally {
    redeeming.value = false
  }
}

function askRevoke(id: string) {
  revokingId.value = id
  confirmRevoke.value = true
}

async function doRevoke() {
  revoking.value = true
  try {
    await revokeVoucher(revokingId.value)
    confirmRevoke.value = false
    await loadVouchers()
  } catch (e) {
    console.error('Failed to revoke voucher', e)
  } finally {
    revoking.value = false
  }
}

async function copyCode(code: string) {
  try {
    await navigator.clipboard.writeText(code)
    copiedCode.value = code
    setTimeout(() => { copiedCode.value = '' }, 2000)
  } catch {
    // fallback
    const el = document.createElement('textarea')
    el.value = code
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    copiedCode.value = code
    setTimeout(() => { copiedCode.value = '' }, 2000)
  }
}

async function copyAllCodes() {
  const text = generatedCodes.value.join('\n')
  await navigator.clipboard.writeText(text)
}

function getPlanName(planId: string) {
  return plans.value.find(p => p.id === planId)?.name || planId
}

function getCustomerName(customerId: string | null) {
  if (!customerId) return '---'
  const c = customers.value.find(cu => cu.id === customerId)
  return c ? c.full_name : customerId
}

function formatDate(d: string | null) {
  if (!d) return '---'
  return new Date(d).toLocaleDateString('en-PH', { year: 'numeric', month: 'short', day: 'numeric' })
}

const filteredCustomers = ref<Customer[]>([])
watch(customerSearch, (q) => {
  if (!q) {
    filteredCustomers.value = customers.value.slice(0, 20)
    return
  }
  const lower = q.toLowerCase()
  filteredCustomers.value = customers.value
    .filter(c => c.full_name.toLowerCase().includes(lower) || c.pppoe_username.toLowerCase().includes(lower))
    .slice(0, 20)
})

watch(filterStatus, () => {
  page.value = 1
  loadVouchers()
})

watch(page, loadVouchers)

onMounted(() => {
  loadVouchers()
  loadPlans()
  loadCustomers()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Vouchers</h1>
        <p class="text-sm text-gray-500 mt-1">Generate and manage prepaid voucher codes</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="openRedeem"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5 2a2 2 0 00-2 2v14l3.5-2 3.5 2 3.5-2 3.5 2V4a2 2 0 00-2-2H5zm4.707 3.707a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L8.414 9H10a3 3 0 013 3v1a1 1 0 102 0v-1a5 5 0 00-5-5H8.414l1.293-1.293z" clip-rule="evenodd"/></svg>
          Redeem
        </button>
        <button
          @click="openGenerate"
          class="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-hover transition-colors"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"/></svg>
          Generate Batch
        </button>
      </div>
    </div>

    <!-- Status Filter -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-4">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-500 mr-2">Status:</span>
        <button
          @click="filterStatus = ''"
          :class="[
            'px-3 py-1.5 text-sm rounded-lg font-medium transition-colors',
            !filterStatus ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          All
        </button>
        <button
          v-for="s in STATUSES"
          :key="s"
          @click="filterStatus = s"
          :class="[
            'px-3 py-1.5 text-sm rounded-lg font-medium transition-colors capitalize',
            filterStatus === s ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          {{ s }}
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm text-left">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50/50">
              <th class="px-4 py-3 font-medium text-gray-500">Code</th>
              <th class="px-4 py-3 font-medium text-gray-500">Duration</th>
              <th class="px-4 py-3 font-medium text-gray-500">Status</th>
              <th class="px-4 py-3 font-medium text-gray-500">Plan</th>
              <th class="px-4 py-3 font-medium text-gray-500">Activated</th>
              <th class="px-4 py-3 font-medium text-gray-500">Expires</th>
              <th class="px-4 py-3 font-medium text-gray-500">Customer</th>
              <th class="px-4 py-3 font-medium text-gray-500 text-right">Actions</th>
            </tr>
          </thead>
          <tbody v-if="loading">
            <tr>
              <td colspan="8" class="px-4 py-12 text-center text-gray-400">
                <svg class="w-6 h-6 animate-spin mx-auto mb-2 text-primary" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                Loading vouchers...
              </td>
            </tr>
          </tbody>
          <tbody v-else-if="vouchers.length === 0">
            <tr>
              <td colspan="8" class="px-4 py-12 text-center text-gray-400">No vouchers found.</td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr v-for="v in vouchers" :key="v.id" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
              <td class="px-4 py-3">
                <code class="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded text-gray-800">{{ v.code }}</code>
              </td>
              <td class="px-4 py-3 text-gray-700">{{ v.duration_days }} days</td>
              <td class="px-4 py-3"><StatusBadge :status="v.status" /></td>
              <td class="px-4 py-3 text-gray-700">{{ getPlanName(v.plan_id) }}</td>
              <td class="px-4 py-3 text-gray-500">{{ formatDate(v.activated_at) }}</td>
              <td class="px-4 py-3 text-gray-500">{{ formatDate(v.expires_at) }}</td>
              <td class="px-4 py-3 text-gray-700">{{ getCustomerName(v.customer_id) }}</td>
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="copyCode(v.code)"
                    class="text-xs font-medium transition-colors"
                    :class="copiedCode === v.code ? 'text-green-600' : 'text-primary hover:text-primary-hover'"
                  >
                    {{ copiedCode === v.code ? 'Copied!' : 'Copy' }}
                  </button>
                  <button
                    v-if="v.status === 'unused'"
                    @click="askRevoke(v.id)"
                    class="text-xs font-medium text-red-600 hover:text-red-700 transition-colors"
                  >
                    Revoke
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pagination :page="page" :page-size="pageSize" :total="total" @update:page="page = $event" />
    </div>

    <!-- Generate Modal -->
    <Modal :open="showGenerateModal" title="Generate Voucher Batch" @close="showGenerateModal = false">
      <form @submit.prevent="doGenerate" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Plan</label>
          <select
            v-model="generateForm.plan_id"
            required
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          >
            <option value="" disabled>Select a plan</option>
            <option v-for="p in plans" :key="p.id" :value="p.id">{{ p.name }} - ₱{{ Number(p.monthly_price).toLocaleString() }}</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Count</label>
            <input
              v-model.number="generateForm.count"
              type="number"
              min="1"
              max="500"
              required
              class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors tabular-nums"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Duration (days)</label>
            <input
              v-model.number="generateForm.duration_days"
              type="number"
              min="1"
              required
              class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors tabular-nums"
            />
          </div>
        </div>
      </form>
      <template #footer>
        <button
          @click="showGenerateModal = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="doGenerate"
          :disabled="generating || !generateForm.plan_id"
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50"
        >
          {{ generating ? 'Generating...' : 'Generate' }}
        </button>
      </template>
    </Modal>

    <!-- Generated Codes Modal -->
    <Modal :open="showCodesModal" title="Vouchers Generated" size="lg" @close="showCodesModal = false">
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <p class="text-sm text-gray-600">{{ generatedCodes.length }} voucher codes have been generated successfully.</p>
          <button
            @click="copyAllCodes"
            class="text-sm font-medium text-primary hover:text-primary-hover transition-colors"
          >
            Copy All
          </button>
        </div>
        <div class="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
            <div
              v-for="code in generatedCodes"
              :key="code"
              class="flex items-center justify-between bg-white rounded-lg border border-gray-200 px-3 py-2"
            >
              <code class="text-sm font-mono text-gray-800">{{ code }}</code>
              <button @click="copyCode(code)" class="ml-2 text-gray-400 hover:text-primary transition-colors">
                <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path d="M8 2a1 1 0 000 2h2a1 1 0 100-2H8z"/><path d="M3 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v6h-4.586l1.293-1.293a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L10.414 13H15v3a2 2 0 01-2 2H5a2 2 0 01-2-2V5z"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button
          @click="showCodesModal = false"
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors"
        >
          Done
        </button>
      </template>
    </Modal>

    <!-- Redeem Modal -->
    <Modal :open="showRedeemModal" title="Redeem Voucher" @close="showRedeemModal = false">
      <form @submit.prevent="doRedeem" class="space-y-4">
        <div v-if="redeemError" class="flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          <svg class="w-5 h-5 shrink-0 mt-0.5 text-red-500" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd"/></svg>
          <span>{{ redeemError }}</span>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Voucher Code</label>
          <input
            v-model="redeemForm.code"
            type="text"
            required
            placeholder="Enter voucher code"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 font-mono focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Customer</label>
          <input
            v-model="customerSearch"
            type="text"
            placeholder="Search by name or username..."
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 mb-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
          <select
            v-model="redeemForm.customer_id"
            required
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          >
            <option value="" disabled>Select a customer</option>
            <option v-for="c in filteredCustomers" :key="c.id" :value="c.id">
              {{ c.full_name }} ({{ c.pppoe_username }})
            </option>
          </select>
        </div>
      </form>
      <template #footer>
        <button
          @click="showRedeemModal = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="doRedeem"
          :disabled="redeeming || !redeemForm.code || !redeemForm.customer_id"
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50"
        >
          {{ redeeming ? 'Redeeming...' : 'Redeem' }}
        </button>
      </template>
    </Modal>

    <!-- Confirm Revoke -->
    <ConfirmDialog
      :open="confirmRevoke"
      title="Revoke Voucher"
      message="Are you sure you want to revoke this voucher? This will make it permanently unusable."
      confirm-text="Revoke"
      :danger="true"
      :loading="revoking"
      @confirm="doRevoke"
      @cancel="confirmRevoke = false"
    />
  </div>
</template>
