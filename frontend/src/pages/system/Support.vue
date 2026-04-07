<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getSupportTickets, updateSupportTicket, type SupportTicket } from '../../api/support'
import StatusBadge from '../../components/common/StatusBadge.vue'

const tickets = ref<SupportTicket[]>([])
const loading = ref(true)
const error = ref('')

// Pagination
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// Filters
const filterStatus = ref('')
const filterCategory = ref('')
const searchQuery = ref('')

// Expanded row
const expandedId = ref<string | null>(null)

// Status update
const updatingId = ref<string | null>(null)

async function loadTickets() {
  loading.value = true
  error.value = ''
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterCategory.value) params.category = filterCategory.value
    if (searchQuery.value) params.search = searchQuery.value

    const { data } = await getSupportTickets(params)
    tickets.value = data.items
    total.value = data.total
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to load support tickets.'
  } finally {
    loading.value = false
  }
}

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

async function changeStatus(ticket: SupportTicket, newStatus: string) {
  updatingId.value = ticket.id
  try {
    const { data } = await updateSupportTicket(ticket.id, { status: newStatus })
    Object.assign(ticket, data)
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Failed to update status')
  } finally {
    updatingId.value = null
  }
}

async function saveNotes(ticket: SupportTicket, notes: string) {
  updatingId.value = ticket.id
  try {
    const { data } = await updateSupportTicket(ticket.id, { admin_notes: notes })
    Object.assign(ticket, data)
  } catch {
    alert('Failed to save notes')
  } finally {
    updatingId.value = null
  }
}

function parseChatHistory(raw: string | null): Array<{ role: string; content: string }> {
  if (!raw) return []
  try {
    return JSON.parse(raw)
  } catch {
    return []
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function categoryColor(cat: string) {
  if (cat === 'bug') return 'bg-red-50 text-red-700 border-red-200'
  if (cat === 'feature_request') return 'bg-blue-50 text-blue-700 border-blue-200'
  return 'bg-gray-50 text-gray-600 border-gray-200'
}

function categoryLabel(cat: string) {
  if (cat === 'bug') return 'Bug'
  if (cat === 'feature_request') return 'Feature Request'
  return 'Question'
}

const statusOptions = ['open', 'in_progress', 'resolved', 'closed']

// Re-fetch on filter/page change
watch([filterStatus, filterCategory, page], loadTickets)

let searchTimeout: ReturnType<typeof setTimeout>
watch(searchQuery, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 1
    loadTickets()
  }, 400)
})

onMounted(loadTickets)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Support Inbox</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        Bug reports and feature requests auto-detected from tenant AI chat
      </p>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search tenant or subject..."
        class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary w-64"
      />
      <select
        v-model="filterStatus"
        class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/30"
      >
        <option value="">All Statuses</option>
        <option value="open">Open</option>
        <option value="in_progress">In Progress</option>
        <option value="resolved">Resolved</option>
        <option value="closed">Closed</option>
      </select>
      <select
        v-model="filterCategory"
        class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/30"
      >
        <option value="">All Categories</option>
        <option value="bug">Bug</option>
        <option value="feature_request">Feature Request</option>
      </select>
      <span class="text-sm text-gray-400 ml-auto">{{ total }} ticket{{ total !== 1 ? 's' : '' }}</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-6 py-4 text-sm text-red-700 dark:text-red-400">
      {{ error }}
    </div>

    <!-- Table -->
    <div v-else class="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/30">
              <th class="text-left font-medium text-gray-500 dark:text-gray-400 px-6 py-3">Date</th>
              <th class="text-left font-medium text-gray-500 dark:text-gray-400 px-6 py-3">Tenant</th>
              <th class="text-left font-medium text-gray-500 dark:text-gray-400 px-6 py-3">Category</th>
              <th class="text-left font-medium text-gray-500 dark:text-gray-400 px-6 py-3">Subject</th>
              <th class="text-left font-medium text-gray-500 dark:text-gray-400 px-6 py-3">Status</th>
              <th class="text-right font-medium text-gray-500 dark:text-gray-400 px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
            <tr v-if="tickets.length === 0">
              <td colspan="6" class="px-6 py-12 text-center text-gray-400 dark:text-gray-500">No support tickets yet.</td>
            </tr>
            <template v-for="ticket in tickets" :key="ticket.id">
              <!-- Main row -->
              <tr
                class="hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-colors cursor-pointer"
                @click="toggleExpand(ticket.id)"
              >
                <td class="px-6 py-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">{{ formatDate(ticket.created_at) }}</td>
                <td class="px-6 py-4">
                  <p class="font-medium text-gray-900 dark:text-gray-100">{{ ticket.tenant_name || '-' }}</p>
                  <p class="text-xs text-gray-400">{{ ticket.tenant_email }}</p>
                </td>
                <td class="px-6 py-4">
                  <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border', categoryColor(ticket.category)]">
                    {{ categoryLabel(ticket.category) }}
                  </span>
                </td>
                <td class="px-6 py-4 text-gray-700 dark:text-gray-300 max-w-xs truncate">{{ ticket.subject }}</td>
                <td class="px-6 py-4">
                  <StatusBadge :status="ticket.status" />
                </td>
                <td class="px-6 py-4 text-right" @click.stop>
                  <select
                    :value="ticket.status"
                    @change="changeStatus(ticket, ($event.target as HTMLSelectElement).value)"
                    :disabled="updatingId === ticket.id"
                    class="px-2 py-1 text-xs rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
                  >
                    <option v-for="s in statusOptions" :key="s" :value="s">{{ s.replace('_', ' ') }}</option>
                  </select>
                </td>
              </tr>

              <!-- Expanded detail row -->
              <tr v-if="expandedId === ticket.id">
                <td colspan="6" class="px-6 py-4 bg-gray-50/70 dark:bg-gray-900/30">
                  <div class="space-y-4 max-w-4xl">
                    <!-- Full description -->
                    <div>
                      <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">Full Message</h4>
                      <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ ticket.description }}</p>
                    </div>

                    <!-- Images -->
                    <div v-if="ticket.image_urls">
                      <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">Attachments</h4>
                      <div class="flex flex-wrap gap-2">
                        <a
                          v-for="(url, idx) in ticket.image_urls.split(',')"
                          :key="idx"
                          :href="url.startsWith('http') ? url : '/' + url"
                          target="_blank"
                          class="text-xs text-primary hover:underline"
                        >
                          Image {{ idx + 1 }}
                        </a>
                      </div>
                    </div>

                    <!-- Chat history -->
                    <div v-if="ticket.chat_history">
                      <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Chat History</h4>
                      <div class="space-y-2 max-h-64 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-600 p-3 bg-white dark:bg-gray-800">
                        <div
                          v-for="(msg, idx) in parseChatHistory(ticket.chat_history)"
                          :key="idx"
                          :class="[
                            'rounded-lg px-3 py-2 text-sm max-w-[80%]',
                            msg.role === 'user'
                              ? 'bg-primary/10 text-gray-800 dark:text-gray-200 ml-auto'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                          ]"
                        >
                          <p class="text-[10px] font-semibold uppercase text-gray-400 mb-0.5">{{ msg.role === 'user' ? 'Tenant' : 'AI' }}</p>
                          <p class="whitespace-pre-wrap">{{ msg.content }}</p>
                        </div>
                      </div>
                    </div>

                    <!-- Admin notes -->
                    <div>
                      <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">Admin Notes</h4>
                      <textarea
                        :value="ticket.admin_notes || ''"
                        @blur="saveNotes(ticket, ($event.target as HTMLTextAreaElement).value)"
                        rows="2"
                        placeholder="Add internal notes..."
                        class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-y"
                      />
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-gray-100 dark:border-gray-700">
        <p class="text-xs text-gray-400">
          Page {{ page }} of {{ totalPages }}
        </p>
        <div class="flex gap-1">
          <button
            @click="page = Math.max(1, page - 1)"
            :disabled="page <= 1"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40"
          >
            Prev
          </button>
          <button
            @click="page = Math.min(totalPages, page + 1)"
            :disabled="page >= totalPages"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
