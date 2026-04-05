<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getOrganizations, deleteUser, type StaffUser } from '../api/users'
import { useImpersonate } from '../composables/useImpersonate'
import StatCard from '../components/common/StatCard.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import dayjs from 'dayjs'

const router = useRouter()
const { enterOrg } = useImpersonate()

const orgs = ref<StaffUser[]>([])
const loading = ref(true)

async function loadData() {
  try {
    const { data } = await getOrganizations()
    orgs.value = data
  } catch (e) {
    console.error('Failed to load organizations', e)
  } finally {
    loading.value = false
  }
}

const activeOrgs = () => orgs.value.filter(o => o.is_active).length
const recentOrgs = () => orgs.value.filter(o => {
  const created = dayjs(o.created_at)
  return dayjs().diff(created, 'day') <= 30
}).length

// Delete
const showDeleteModal = ref(false)
const deleteTarget = ref<StaffUser | null>(null)
const deleteConfirmText = ref('')
const deleteLoading = ref(false)

function openDelete(org: StaffUser) {
  deleteTarget.value = org
  deleteConfirmText.value = ''
  showDeleteModal.value = true
}

async function handleDelete() {
  if (!deleteTarget.value || deleteConfirmText.value !== deleteTarget.value.username) return
  deleteLoading.value = true
  try {
    await deleteUser(deleteTarget.value.id)
    orgs.value = orgs.value.filter(o => o.id !== deleteTarget.value!.id)
    showDeleteModal.value = false
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Failed to delete')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Platform Overview</h1>
      <p class="text-sm text-gray-500 mt-0.5">NetLedger SaaS — 2max Tech</p>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <template v-else>
      <!-- Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Total Organizations" :value="orgs.length" color="orange">
          <template #icon>
            <svg class="w-5 h-5 text-orange-600" viewBox="0 0 20 20" fill="currentColor"><path d="M4 16.5v-13h-.25a.75.75 0 010-1.5h12.5a.75.75 0 010 1.5H16v13h.25a.75.75 0 010 1.5h-3.5a.75.75 0 01-.75-.75v-2.5a.75.75 0 00-.75-.75h-2.5a.75.75 0 00-.75.75v2.5a.75.75 0 01-.75.75h-3.5a.75.75 0 010-1.5H4zM7 5a.75.75 0 000 1.5h.5a.75.75 0 000-1.5H7zm2.75 0a.75.75 0 000 1.5h.5a.75.75 0 000-1.5h-.5zm2.75 0a.75.75 0 000 1.5h.5a.75.75 0 000-1.5h-.5zM7 8.5a.75.75 0 000 1.5h.5a.75.75 0 000-1.5H7zm2.75 0a.75.75 0 000 1.5h.5a.75.75 0 000-1.5h-.5zm2.75 0a.75.75 0 000 1.5h.5a.75.75 0 000-1.5h-.5zM7 12a.75.75 0 000 1.5h.5a.75.75 0 000-1.5H7zm2.75 0a.75.75 0 000 1.5h.5a.75.75 0 000-1.5h-.5zm2.75 0a.75.75 0 000 1.5h.5a.75.75 0 000-1.5h-.5z"/></svg>
          </template>
        </StatCard>
        <StatCard title="Active" :value="activeOrgs()" color="green">
          <template #icon>
            <svg class="w-5 h-5 text-green-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>
          </template>
        </StatCard>
        <StatCard title="New This Month" :value="recentOrgs()" color="blue">
          <template #icon>
            <svg class="w-5 h-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor"><path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z"/></svg>
          </template>
        </StatCard>
      </div>

      <!-- Recent Organizations -->
      <div class="rounded-xl bg-white shadow-sm border border-gray-100">
        <div class="px-6 py-4 border-b border-gray-100">
          <h2 class="text-sm font-semibold text-gray-900">Registered Organizations</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-100">
                <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Admin</th>
                <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
                <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Registered</th>
                <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-if="!orgs.length">
                <td colspan="6" class="px-6 py-12 text-center text-sm text-gray-400">No organizations registered yet</td>
              </tr>
              <tr v-for="org in orgs" :key="org.id" class="hover:bg-gray-50/50 transition-colors">
                <td class="px-6 py-4">
                  <p class="text-sm font-medium text-gray-900">{{ org.company_name || 'Unnamed' }}</p>
                  <p class="text-xs text-gray-400">{{ org.email }}</p>
                </td>
                <td class="px-6 py-4">
                  <p class="text-sm text-gray-700">{{ org.full_name || org.username }}</p>
                  <p class="text-xs text-gray-400 font-mono">{{ org.username }}</p>
                </td>
                <td class="px-6 py-4">
                  <p class="text-sm text-gray-700">{{ org.phone || '—' }}</p>
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                  {{ dayjs(org.created_at).format('MMM D, YYYY') }}
                </td>
                <td class="px-6 py-4">
                  <StatusBadge :status="org.is_active ? 'active' : 'inactive'" />
                </td>
                <td class="px-6 py-4 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      @click="enterOrg({ id: org.id, username: org.username, company_name: org.company_name || org.username }); router.push('/dashboard')"
                      class="px-3 py-1.5 text-xs font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors"
                    >
                      Manage
                    </button>
                    <button
                      @click="openDelete(org)"
                      class="px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Delete Modal -->
    <Teleport to="body">
      <div v-if="showDeleteModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="showDeleteModal = false" />
        <div class="relative w-full max-w-sm bg-white rounded-xl shadow-2xl p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Delete Organization</h3>
          <div class="flex items-start gap-3 rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
            <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>
            <p class="text-sm text-red-800">This will permanently delete <strong>{{ deleteTarget?.company_name }}</strong> and all their data (customers, invoices, routers, settings).</p>
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Type <strong class="font-mono text-red-600">{{ deleteTarget?.username }}</strong> to confirm</label>
            <input v-model="deleteConfirmText" type="text" class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-red-300 focus:border-red-400" />
          </div>
          <div class="flex justify-end gap-3">
            <button @click="showDeleteModal = false" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
            <button @click="handleDelete" :disabled="deleteLoading || deleteConfirmText !== deleteTarget?.username" class="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg disabled:opacity-40">
              {{ deleteLoading ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
