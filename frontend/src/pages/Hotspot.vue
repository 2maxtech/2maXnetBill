<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getHotspotUsers, getHotspotSessions } from '../api/network'
import { getRouters, type RouterType } from '../api/routers'

interface HotspotUser {
  '.id': string
  name: string
  profile: string
  password?: string
  disabled: string
  'limit-bytes-total'?: string
  'bytes-in'?: string
  'bytes-out'?: string
}

interface HotspotSession {
  '.id': string
  user: string
  address: string
  'mac-address': string
  uptime: string
  'bytes-in': string
  'bytes-out': string
}

const routers = ref<RouterType[]>([])
const selectedRouter = ref('')
const activeTab = ref<'users' | 'sessions'>('users')

const users = ref<HotspotUser[]>([])
const sessions = ref<HotspotSession[]>([])
const loadingUsers = ref(false)
const loadingSessions = ref(false)

async function loadRouters() {
  try {
    const { data } = await getRouters()
    routers.value = data.filter(r => r.is_active)
    if (routers.value.length > 0 && !selectedRouter.value) {
      selectedRouter.value = routers.value[0].id
    }
  } catch (e) {
    console.error('Failed to load routers', e)
  }
}

async function loadUsers() {
  if (!selectedRouter.value) return
  loadingUsers.value = true
  try {
    const { data } = await getHotspotUsers(selectedRouter.value)
    users.value = (data.users || data) as HotspotUser[]
  } catch (e) {
    console.error('Failed to load hotspot users', e)
  } finally {
    loadingUsers.value = false
  }
}

async function loadSessions() {
  if (!selectedRouter.value) return
  loadingSessions.value = true
  try {
    const { data } = await getHotspotSessions(selectedRouter.value)
    sessions.value = (data.sessions || data) as HotspotSession[]
  } catch (e) {
    console.error('Failed to load hotspot sessions', e)
  } finally {
    loadingSessions.value = false
  }
}

function formatBytes(bytes: string | undefined): string {
  if (!bytes) return '---'
  const b = parseInt(bytes, 10)
  if (isNaN(b) || b === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(b) / Math.log(1024))
  return (b / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

function loadTabData() {
  if (activeTab.value === 'users') {
    loadUsers()
  } else {
    loadSessions()
  }
}

watch(selectedRouter, () => {
  loadTabData()
})

watch(activeTab, () => {
  loadTabData()
})

onMounted(async () => {
  await loadRouters()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Hotspot Management</h1>
        <p class="text-sm text-gray-500 mt-1">Manage hotspot users and view active sessions</p>
      </div>
      <div class="flex items-center gap-3">
        <label class="text-sm font-medium text-gray-500">Router:</label>
        <select
          v-model="selectedRouter"
          class="rounded-lg border border-gray-300 text-sm px-3 py-2.5 min-w-[200px] focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
        >
          <option value="" disabled>Select a router</option>
          <option v-for="r in routers" :key="r.id" :value="r.id">{{ r.name }} - {{ r.location || r.url }}</option>
        </select>
      </div>
    </div>

    <!-- Tabs -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      <div class="border-b border-gray-100">
        <div class="flex">
          <button
            @click="activeTab = 'users'"
            :class="[
              'px-6 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'users'
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/></svg>
              Users
              <span class="bg-gray-100 text-gray-600 text-xs font-semibold rounded-full px-2 py-0.5 tabular-nums">{{ users.length }}</span>
            </div>
          </button>
          <button
            @click="activeTab = 'sessions'"
            :class="[
              'px-6 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'sessions'
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
              Active Sessions
              <span class="bg-gray-100 text-gray-600 text-xs font-semibold rounded-full px-2 py-0.5 tabular-nums">{{ sessions.length }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- Users Tab -->
      <div v-if="activeTab === 'users'">
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-left">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50/50">
                <th class="px-4 py-3 font-medium text-gray-500">Name</th>
                <th class="px-4 py-3 font-medium text-gray-500">Profile</th>
                <th class="px-4 py-3 font-medium text-gray-500">Password</th>
                <th class="px-4 py-3 font-medium text-gray-500">Status</th>
                <th class="px-4 py-3 font-medium text-gray-500">Data Limit</th>
                <th class="px-4 py-3 font-medium text-gray-500">Bytes In</th>
                <th class="px-4 py-3 font-medium text-gray-500">Bytes Out</th>
              </tr>
            </thead>
            <tbody v-if="loadingUsers">
              <tr>
                <td colspan="7" class="px-4 py-12 text-center text-gray-400">
                  <svg class="w-6 h-6 animate-spin mx-auto mb-2 text-primary" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                  Loading users...
                </td>
              </tr>
            </tbody>
            <tbody v-else-if="users.length === 0">
              <tr>
                <td colspan="7" class="px-4 py-12 text-center text-gray-400">No hotspot users found.</td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr v-for="u in users" :key="u['.id']" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-3 font-medium text-gray-900">{{ u.name }}</td>
                <td class="px-4 py-3 text-gray-700">{{ u.profile }}</td>
                <td class="px-4 py-3">
                  <code class="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded text-gray-600">{{ u.password || '***' }}</code>
                </td>
                <td class="px-4 py-3">
                  <span
                    :class="[
                      'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium',
                      u.disabled === 'true' || u.disabled === 'yes'
                        ? 'bg-red-50 text-red-700'
                        : 'bg-green-50 text-green-700'
                    ]"
                  >
                    <span
                      :class="[
                        'w-1.5 h-1.5 rounded-full',
                        u.disabled === 'true' || u.disabled === 'yes' ? 'bg-red-500' : 'bg-green-500'
                      ]"
                    />
                    {{ u.disabled === 'true' || u.disabled === 'yes' ? 'Disabled' : 'Enabled' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-gray-500 tabular-nums">{{ formatBytes(u['limit-bytes-total']) }}</td>
                <td class="px-4 py-3 text-gray-500 tabular-nums">{{ formatBytes(u['bytes-in']) }}</td>
                <td class="px-4 py-3 text-gray-500 tabular-nums">{{ formatBytes(u['bytes-out']) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="px-4 py-3 border-t border-gray-100 text-sm text-gray-500">
          {{ users.length }} user{{ users.length !== 1 ? 's' : '' }}
        </div>
      </div>

      <!-- Sessions Tab -->
      <div v-if="activeTab === 'sessions'">
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-left">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50/50">
                <th class="px-4 py-3 font-medium text-gray-500">User</th>
                <th class="px-4 py-3 font-medium text-gray-500">IP Address</th>
                <th class="px-4 py-3 font-medium text-gray-500">MAC Address</th>
                <th class="px-4 py-3 font-medium text-gray-500">Uptime</th>
                <th class="px-4 py-3 font-medium text-gray-500">Bytes In</th>
                <th class="px-4 py-3 font-medium text-gray-500">Bytes Out</th>
              </tr>
            </thead>
            <tbody v-if="loadingSessions">
              <tr>
                <td colspan="6" class="px-4 py-12 text-center text-gray-400">
                  <svg class="w-6 h-6 animate-spin mx-auto mb-2 text-primary" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                  Loading sessions...
                </td>
              </tr>
            </tbody>
            <tbody v-else-if="sessions.length === 0">
              <tr>
                <td colspan="6" class="px-4 py-12 text-center text-gray-400">No active hotspot sessions.</td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr v-for="s in sessions" :key="s['.id']" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-3 font-medium text-gray-900">{{ s.user }}</td>
                <td class="px-4 py-3">
                  <code class="text-sm font-mono text-gray-700">{{ s.address }}</code>
                </td>
                <td class="px-4 py-3">
                  <code class="text-sm font-mono text-gray-500">{{ s['mac-address'] }}</code>
                </td>
                <td class="px-4 py-3">
                  <span class="inline-flex items-center gap-1 text-gray-700">
                    <svg class="w-3.5 h-3.5 text-green-500" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/></svg>
                    {{ s.uptime }}
                  </span>
                </td>
                <td class="px-4 py-3 text-gray-500 tabular-nums">{{ formatBytes(s['bytes-in']) }}</td>
                <td class="px-4 py-3 text-gray-500 tabular-nums">{{ formatBytes(s['bytes-out']) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="px-4 py-3 border-t border-gray-100 text-sm text-gray-500">
          {{ sessions.length }} active session{{ sessions.length !== 1 ? 's' : '' }}
        </div>
      </div>
    </div>
  </div>
</template>
