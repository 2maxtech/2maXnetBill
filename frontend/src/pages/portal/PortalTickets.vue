<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import { useRouter, useRoute } from 'vue-router'
import { getPortalTickets, createPortalTicket } from '../../api/portal'
import StatusBadge from '../../components/common/StatusBadge.vue'
import Modal from '../../components/common/Modal.vue'

const router = useRouter()
const route = useRoute()
const slug = route.params.slug as string

const tickets = ref<any[]>([])
const loading = ref(false)

// New ticket modal
const showNewTicket = ref(false)
const newTicketForm = ref({ subject: '', priority: 'medium', message: '' })
const createLoading = ref(false)
const createError = ref('')

async function fetchTickets() {
  loading.value = true
  try {
    const { data } = await getPortalTickets()
    tickets.value = Array.isArray(data) ? data : data.items || []
  } catch (e) {
    console.error('Failed to fetch tickets', e)
  } finally {
    loading.value = false
  }
}

function openNewTicket() {
  newTicketForm.value = { subject: '', priority: 'medium', message: '' }
  createError.value = ''
  showNewTicket.value = true
}

async function handleCreate() {
  if (!newTicketForm.value.subject.trim() || !newTicketForm.value.message.trim()) {
    createError.value = 'Subject and message are required.'
    return
  }
  createLoading.value = true
  createError.value = ''
  try {
    await createPortalTicket(newTicketForm.value)
    showNewTicket.value = false
    fetchTickets()
  } catch (e: any) {
    createError.value = e.response?.data?.detail || 'Failed to create ticket'
  } finally {
    createLoading.value = false
  }
}

function goToTicket(ticket: any) {
  router.push(`/portal/${slug}/tickets/${ticket.id}`)
}

onMounted(fetchTickets)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <h1 class="text-2xl font-bold text-gray-900">My Tickets</h1>
      <button
        @click="openNewTicket"
        class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors"
      >
        New Ticket
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Subject</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Status</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Priority</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Created</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <!-- Loading -->
            <template v-if="loading">
              <tr v-for="i in 3" :key="i">
                <td v-for="j in 4" :key="j" class="px-4 py-3">
                  <div class="h-4 bg-gray-100 rounded animate-pulse" />
                </td>
              </tr>
            </template>
            <!-- Empty -->
            <tr v-else-if="!tickets.length">
              <td colspan="4" class="px-4 py-12 text-center text-gray-400">No tickets yet</td>
            </tr>
            <!-- Rows -->
            <tr
              v-else
              v-for="ticket in tickets"
              :key="ticket.id"
              @click="goToTicket(ticket)"
              class="hover:bg-gray-50/50 transition-colors cursor-pointer"
            >
              <td class="px-4 py-3 text-sm text-gray-700 font-medium">{{ ticket.subject }}</td>
              <td class="px-4 py-3"><StatusBadge :status="ticket.status" /></td>
              <td class="px-4 py-3"><StatusBadge :status="ticket.priority" /></td>
              <td class="px-4 py-3 text-sm text-gray-500">{{ dayjs(ticket.created_at).format('MMM D, YYYY h:mm A') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- New Ticket Modal -->
    <Modal :open="showNewTicket" title="New Ticket" size="lg" @close="showNewTicket = false">
      <div
        v-if="createError"
        class="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700"
      >
        {{ createError }}
      </div>
      <form @submit.prevent="handleCreate" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Subject</label>
          <input
            v-model="newTicketForm.subject"
            type="text"
            required
            placeholder="Brief description of your issue"
            class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Priority</label>
          <select
            v-model="newTicketForm.priority"
            class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Message</label>
          <textarea
            v-model="newTicketForm.message"
            rows="5"
            required
            placeholder="Describe your issue in detail..."
            class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors resize-none"
          />
        </div>
      </form>
      <template #footer>
        <button
          @click="showNewTicket = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="handleCreate"
          :disabled="createLoading"
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50"
        >
          {{ createLoading ? 'Creating...' : 'Submit Ticket' }}
        </button>
      </template>
    </Modal>
  </div>
</template>
