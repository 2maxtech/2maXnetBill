<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import Modal from '../components/common/Modal.vue'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import Pagination from '../components/common/Pagination.vue'
import {
  getExpenses,
  createExpense,
  updateExpense,
  deleteExpense,
  getExpenseSummary,
  type ExpenseType,
  type ExpenseSummary,
} from '../api/expenses'

const CATEGORIES = ['electricity', 'internet', 'salary', 'equipment', 'maintenance', 'rent', 'other']
const CATEGORY_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  electricity: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: 'bg-yellow-500' },
  internet: { bg: 'bg-blue-100', text: 'text-blue-700', icon: 'bg-blue-500' },
  salary: { bg: 'bg-green-100', text: 'text-green-700', icon: 'bg-green-500' },
  equipment: { bg: 'bg-purple-100', text: 'text-purple-700', icon: 'bg-purple-500' },
  maintenance: { bg: 'bg-orange-100', text: 'text-orange-700', icon: 'bg-orange-500' },
  rent: { bg: 'bg-cyan-100', text: 'text-cyan-700', icon: 'bg-cyan-500' },
  other: { bg: 'bg-gray-100', text: 'text-gray-700', icon: 'bg-gray-500' },
}

const expenses = ref<ExpenseType[]>([])
const summary = ref<ExpenseSummary[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)

const filterCategory = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')

const showModal = ref(false)
const editingExpense = ref<ExpenseType | null>(null)
const saving = ref(false)
const form = reactive({
  category: 'electricity',
  description: '',
  amount: '',
  date: new Date().toISOString().slice(0, 10),
  receipt_number: '',
})

const confirmDelete = ref(false)
const deletingId = ref('')
const deleting = ref(false)

async function loadExpenses() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize }
    if (filterCategory.value) params.category = filterCategory.value
    if (filterDateFrom.value) params.date_from = filterDateFrom.value
    if (filterDateTo.value) params.date_to = filterDateTo.value
    const { data } = await getExpenses(params)
    expenses.value = data.items
    total.value = data.total
  } catch (e) {
    console.error('Failed to load expenses', e)
  } finally {
    loading.value = false
  }
}

async function loadSummary() {
  try {
    const params: Record<string, any> = {}
    if (filterDateFrom.value) params.date_from = filterDateFrom.value
    if (filterDateTo.value) params.date_to = filterDateTo.value
    const { data } = await getExpenseSummary(params)
    const raw = data as any
    if (Array.isArray(raw)) {
      summary.value = raw
    } else if (raw.by_category) {
      summary.value = Object.entries(raw.by_category).map(([category, total]) => ({ category, total: total as number }))
    } else {
      summary.value = []
    }
  } catch (e) {
    console.error('Failed to load summary', e)
  }
}

function openAdd() {
  editingExpense.value = null
  form.category = 'electricity'
  form.description = ''
  form.amount = ''
  form.date = new Date().toISOString().slice(0, 10)
  form.receipt_number = ''
  showModal.value = true
}

function openEdit(expense: ExpenseType) {
  editingExpense.value = expense
  form.category = expense.category
  form.description = expense.description
  form.amount = String(expense.amount)
  form.date = expense.date.slice(0, 10)
  form.receipt_number = expense.receipt_number || ''
  showModal.value = true
}

async function saveExpense() {
  saving.value = true
  try {
    const payload = {
      category: form.category,
      description: form.description,
      amount: parseFloat(form.amount),
      date: form.date,
      receipt_number: form.receipt_number || null,
    }
    if (editingExpense.value) {
      await updateExpense(editingExpense.value.id, payload)
    } else {
      await createExpense(payload)
    }
    showModal.value = false
    await Promise.all([loadExpenses(), loadSummary()])
  } catch (e) {
    console.error('Failed to save expense', e)
  } finally {
    saving.value = false
  }
}

function askDelete(id: string) {
  deletingId.value = id
  confirmDelete.value = true
}

async function doDelete() {
  deleting.value = true
  try {
    await deleteExpense(deletingId.value)
    confirmDelete.value = false
    await Promise.all([loadExpenses(), loadSummary()])
  } catch (e) {
    console.error('Failed to delete expense', e)
  } finally {
    deleting.value = false
  }
}

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function formatCurrency(v: number | string) {
  return '₱' + Number(v).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

watch([filterCategory, filterDateFrom, filterDateTo], () => {
  page.value = 1
  loadExpenses()
  loadSummary()
})

watch(page, loadExpenses)

onMounted(() => {
  loadExpenses()
  loadSummary()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Expenses</h1>
        <p class="text-sm text-gray-500 mt-1">Track and manage operational expenses</p>
      </div>
      <button
        @click="openAdd"
        class="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-hover transition-colors"
      >
        <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"/></svg>
        Add Expense
      </button>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-4">
      <div
        v-for="cat in CATEGORIES"
        :key="cat"
        class="rounded-xl bg-white shadow-sm border border-gray-100 p-4 hover:-translate-y-0.5 hover:shadow-md transition-all duration-200"
      >
        <div class="flex items-center gap-2 mb-2">
          <span :class="['w-2.5 h-2.5 rounded-full', CATEGORY_COLORS[cat]?.icon]" />
          <span class="text-xs font-medium text-gray-500 uppercase tracking-wider">{{ capitalize(cat) }}</span>
        </div>
        <p class="text-lg font-bold text-gray-900 tabular-nums">
          {{ formatCurrency(summary.find(s => s.category === cat)?.total ?? 0) }}
        </p>
      </div>
    </div>

    <!-- Filters -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-4">
      <div class="flex flex-wrap items-center gap-4">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Category</label>
          <select
            v-model="filterCategory"
            class="rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          >
            <option value="">All Categories</option>
            <option v-for="c in CATEGORIES" :key="c" :value="c">{{ capitalize(c) }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">From</label>
          <input
            v-model="filterDateFrom"
            type="date"
            class="rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">To</label>
          <input
            v-model="filterDateTo"
            type="date"
            class="rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
        <div class="flex items-end">
          <button
            v-if="filterCategory || filterDateFrom || filterDateTo"
            @click="filterCategory = ''; filterDateFrom = ''; filterDateTo = ''"
            class="text-sm text-gray-500 hover:text-gray-700 underline mt-5"
          >
            Clear filters
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm text-left">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50/50">
              <th class="px-4 py-3 font-medium text-gray-500">Category</th>
              <th class="px-4 py-3 font-medium text-gray-500">Description</th>
              <th class="px-4 py-3 font-medium text-gray-500 text-right">Amount</th>
              <th class="px-4 py-3 font-medium text-gray-500">Date</th>
              <th class="px-4 py-3 font-medium text-gray-500">Receipt #</th>
              <th class="px-4 py-3 font-medium text-gray-500 text-right">Actions</th>
            </tr>
          </thead>
          <tbody v-if="loading">
            <tr>
              <td colspan="6" class="px-4 py-12 text-center text-gray-400">
                <svg class="w-6 h-6 animate-spin mx-auto mb-2 text-primary" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                Loading expenses...
              </td>
            </tr>
          </tbody>
          <tbody v-else-if="expenses.length === 0">
            <tr>
              <td colspan="6" class="px-4 py-12 text-center text-gray-400">No expenses found.</td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr v-for="exp in expenses" :key="exp.id" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
              <td class="px-4 py-3">
                <span :class="['inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium', CATEGORY_COLORS[exp.category]?.bg, CATEGORY_COLORS[exp.category]?.text]">
                  <span :class="['w-1.5 h-1.5 rounded-full', CATEGORY_COLORS[exp.category]?.icon]" />
                  {{ capitalize(exp.category) }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-700">{{ exp.description }}</td>
              <td class="px-4 py-3 text-gray-900 font-medium text-right tabular-nums">{{ formatCurrency(exp.amount) }}</td>
              <td class="px-4 py-3 text-gray-500">{{ exp.date.slice(0, 10) }}</td>
              <td class="px-4 py-3 text-gray-500">{{ exp.receipt_number || '---' }}</td>
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button @click="openEdit(exp)" class="text-xs font-medium text-primary hover:text-primary-hover transition-colors">Edit</button>
                  <button @click="askDelete(exp.id)" class="text-xs font-medium text-red-600 hover:text-red-700 transition-colors">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pagination :page="page" :page-size="pageSize" :total="total" @update:page="page = $event" />
    </div>

    <!-- Add/Edit Modal -->
    <Modal :open="showModal" :title="editingExpense ? 'Edit Expense' : 'Add Expense'" @close="showModal = false">
      <form @submit.prevent="saveExpense" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Category</label>
          <select
            v-model="form.category"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          >
            <option v-for="c in CATEGORIES" :key="c" :value="c">{{ capitalize(c) }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
          <input
            v-model="form.description"
            type="text"
            required
            placeholder="e.g. Monthly electricity bill"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Amount (₱)</label>
            <input
              v-model="form.amount"
              type="number"
              step="0.01"
              min="0"
              required
              placeholder="0.00"
              class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors tabular-nums"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Date</label>
            <input
              v-model="form.date"
              type="date"
              required
              class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
            />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Receipt Number <span class="text-gray-400">(optional)</span></label>
          <input
            v-model="form.receipt_number"
            type="text"
            placeholder="e.g. REC-001"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
      </form>
      <template #footer>
        <button
          @click="showModal = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="saveExpense"
          :disabled="saving || !form.description || !form.amount"
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : editingExpense ? 'Update' : 'Add Expense' }}
        </button>
      </template>
    </Modal>

    <!-- Confirm Delete -->
    <ConfirmDialog
      :open="confirmDelete"
      title="Delete Expense"
      message="Are you sure you want to delete this expense? This action cannot be undone."
      confirm-text="Delete"
      :danger="true"
      :loading="deleting"
      @confirm="doDelete"
      @cancel="confirmDelete = false"
    />
  </div>
</template>
