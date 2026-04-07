<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import dayjs from 'dayjs'
import api from '../../api/client'

interface LogEntry {
  id: string
  action: string
  entity_type?: string
  details: string | null
  user_id: string | null
  ip_address?: string | null
  created_at: string
}

const logs = ref<LogEntry[]>([])
const loading = ref(false)
const filterAction = ref('all')
const limit = ref(100)
const autoRefresh = ref(false)
let refreshInterval: ReturnType<typeof setInterval> | null = null
const expandedRows = ref<Set<string>>(new Set())

const actionFilters = [
  { value: 'all', label: 'All Actions' },
  { value: 'create', label: 'Create' },
  { value: 'update', label: 'Update' },
  { value: 'delete', label: 'Delete' },
  { value: 'login', label: 'Login' },
  { value: 'throttle', label: 'Throttle' },
  { value: 'disconnect', label: 'Disconnect' },
  { value: 'reconnect', label: 'Reconnect' },
  { value: 'import', label: 'Import' },
]

async function fetchLogs() {
  loading.value = true
  try {
    const params: Record<string, any> = { limit: limit.value }
    if (filterAction.value !== 'all') params.level = filterAction.value
    const { data } = await api.get<LogEntry[]>('/system/logs', { params })
    logs.value = data
  } catch (e) {
    console.error('Failed to fetch system logs', e)
  } finally {
    loading.value = false
  }
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    refreshInterval = setInterval(fetchLogs, 10000)
  } else if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

function toggleRow(id: string) {
  if (expandedRows.value.has(id)) {
    expandedRows.value.delete(id)
  } else {
    expandedRows.value.add(id)
  }
}

function shortId(id: string | null) {
  if (!id) return '-'
  return id.substring(0, 8)
}

function actionBadgeClass(action: string): string {
  const map: Record<string, string> = {
    create: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    update: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    delete: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    login: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    throttle: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    disconnect: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    reconnect: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    import: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
  }
  return map[action] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

onMounted(fetchLogs)

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">System Logs</h1>

    <!-- Filters -->
    <div class="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-4">
      <div class="flex flex-wrap items-end gap-4">
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Action</label>
          <select
            v-model="filterAction"
            class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          >
            <option v-for="af in actionFilters" :key="af.value" :value="af.value">{{ af.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Limit</label>
          <select
            v-model="limit"
            class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          >
            <option :value="50">50</option>
            <option :value="100">100</option>
            <option :value="200">200</option>
            <option :value="500">500</option>
          </select>
        </div>
        <button
          @click="fetchLogs"
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors"
        >
          Filter
        </button>
        <button
          @click="toggleAutoRefresh"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            autoRefresh
              ? 'bg-green-600 text-white hover:bg-green-700'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
          ]"
        >
          <span class="flex items-center gap-2">
            <span v-if="autoRefresh" class="w-2 h-2 rounded-full bg-white animate-pulse" />
            {{ autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-750 border-b border-gray-100 dark:border-gray-700">
              <th class="px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider text-left w-8"></th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider text-left">Timestamp</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider text-left">User</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider text-left">Action</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider text-left">Entity Type</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider text-left">IP Address</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
            <!-- Loading -->
            <template v-if="loading">
              <tr v-for="i in 5" :key="i">
                <td v-for="j in 6" :key="j" class="px-4 py-3">
                  <div class="h-4 bg-gray-100 dark:bg-gray-700 rounded animate-pulse" />
                </td>
              </tr>
            </template>
            <!-- Empty -->
            <tr v-else-if="!logs.length">
              <td colspan="6" class="px-4 py-12 text-center text-gray-400 dark:text-gray-500">No log entries found</td>
            </tr>
            <!-- Rows -->
            <template v-else v-for="log in logs" :key="log.id">
              <tr
                @click="toggleRow(log.id)"
                class="hover:bg-gray-50/50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
              >
                <td class="px-4 py-3 text-sm text-gray-400">
                  <svg
                    :class="['w-4 h-4 transition-transform', expandedRows.has(log.id) ? 'rotate-90' : '']"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" />
                  </svg>
                </td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ dayjs(log.created_at).format('MMM D, YYYY h:mm A') }}</td>
                <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 font-mono">{{ shortId(log.user_id) }}</td>
                <td class="px-4 py-3">
                  <span :class="['inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', actionBadgeClass(log.action)]">
                    {{ log.action }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                    {{ log.entity_type || '-' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{{ log.ip_address || '-' }}</td>
              </tr>
              <!-- Expanded Details -->
              <tr v-if="expandedRows.has(log.id)">
                <td colspan="6" class="px-4 py-4 bg-gray-50 dark:bg-gray-750">
                  <div class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">Details</div>
                  <pre class="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-4 overflow-x-auto whitespace-pre-wrap">{{ log.details ? (typeof log.details === 'string' ? log.details : JSON.stringify(log.details, null, 2)) : 'No details' }}</pre>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
