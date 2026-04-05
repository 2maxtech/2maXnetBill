<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getOrganizations, updateUser, deleteUser, type StaffUser } from '../../api/users'
import { useImpersonate } from '../../composables/useImpersonate'
import Modal from '../../components/common/Modal.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'

const router = useRouter()
const { enterOrg } = useImpersonate()

const organizations = ref<StaffUser[]>([])
const loading = ref(true)
const error = ref('')

// Reset password modal
const showResetModal = ref(false)
const resetOrg = ref<StaffUser | null>(null)
const newPassword = ref('')
const resetLoading = ref(false)
const resetMsg = ref('')
const resetMsgType = ref<'success' | 'error'>('success')

// Toggle active modal
const toggleOrg = ref<StaffUser | null>(null)
const toggleLoading = ref(false)

async function loadOrgs() {
  try {
    const { data } = await getOrganizations()
    organizations.value = data
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to load organizations.'
  } finally {
    loading.value = false
  }
}

function openResetPassword(org: StaffUser) {
  resetOrg.value = org
  newPassword.value = ''
  resetMsg.value = ''
  showResetModal.value = true
}

async function handleResetPassword() {
  if (!resetOrg.value || !newPassword.value) return
  if (newPassword.value.length < 6) {
    resetMsg.value = 'Password must be at least 6 characters'
    resetMsgType.value = 'error'
    return
  }
  resetLoading.value = true
  resetMsg.value = ''
  try {
    await updateUser(resetOrg.value.id, { password: newPassword.value })
    resetMsg.value = 'Password reset successfully'
    resetMsgType.value = 'success'
    newPassword.value = ''
  } catch (e: any) {
    resetMsg.value = e.response?.data?.detail || 'Failed to reset password'
    resetMsgType.value = 'error'
  } finally {
    resetLoading.value = false
  }
}

async function toggleActive(org: StaffUser) {
  toggleLoading.value = true
  try {
    await updateUser(org.id, { is_active: !org.is_active })
    org.is_active = !org.is_active
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Failed to update status')
  } finally {
    toggleLoading.value = false
  }
}

// Delete org
const showDeleteModal = ref(false)
const deleteOrg = ref<StaffUser | null>(null)
const deleteConfirmText = ref('')
const deleteLoading = ref(false)

function openDeleteOrg(org: StaffUser) {
  deleteOrg.value = org
  deleteConfirmText.value = ''
  showDeleteModal.value = true
}

async function handleDeleteOrg() {
  if (!deleteOrg.value) return
  if (deleteConfirmText.value !== deleteOrg.value.username) return
  deleteLoading.value = true
  try {
    await deleteUser(deleteOrg.value.id)
    organizations.value = organizations.value.filter(o => o.id !== deleteOrg.value!.id)
    showDeleteModal.value = false
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Failed to delete organization')
  } finally {
    deleteLoading.value = false
  }
}

function manageOrg(org: StaffUser) {
  enterOrg({ id: org.id, username: org.username, company_name: org.company_name || org.username })
  router.push('/dashboard')
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

function generatePassword() {
  const chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
  newPassword.value = Array.from({ length: 12 }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

onMounted(loadOrgs)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Organizations</h1>
      <p class="text-sm text-gray-500 mt-1">All registered ISP operators on the platform</p>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="error" class="rounded-xl bg-red-50 border border-red-200 px-6 py-4 text-sm text-red-700">{{ error }}</div>

    <div v-else class="rounded-xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50/50">
              <th class="text-left font-medium text-gray-500 px-6 py-3">Company</th>
              <th class="text-left font-medium text-gray-500 px-6 py-3">Admin</th>
              <th class="text-left font-medium text-gray-500 px-6 py-3">Contact</th>
              <th class="text-left font-medium text-gray-500 px-6 py-3">Registered</th>
              <th class="text-left font-medium text-gray-500 px-6 py-3">Status</th>
              <th class="text-right font-medium text-gray-500 px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-if="organizations.length === 0">
              <td colspan="6" class="px-6 py-12 text-center text-gray-400">No organizations registered yet.</td>
            </tr>
            <tr v-for="org in organizations" :key="org.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-6 py-4">
                <p class="font-medium text-gray-900">{{ org.company_name || '-' }}</p>
                <p class="text-xs text-gray-400">{{ org.email }}</p>
              </td>
              <td class="px-6 py-4">
                <p class="text-gray-700">{{ org.full_name || org.username }}</p>
                <p v-if="org.full_name" class="text-xs text-gray-400 font-mono">{{ org.username }}</p>
              </td>
              <td class="px-6 py-4 text-gray-600">{{ org.phone || '-' }}</td>
              <td class="px-6 py-4 text-gray-500">{{ formatDate(org.created_at) }}</td>
              <td class="px-6 py-4">
                <StatusBadge :status="org.is_active ? 'active' : 'inactive'" />
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-2">
                  <button @click="manageOrg(org)" class="px-3 py-1.5 text-xs font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors">
                    Manage
                  </button>
                  <button @click="openResetPassword(org)" class="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                    Reset Password
                  </button>
                  <button @click="toggleActive(org)" :disabled="toggleLoading" :class="[
                    'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
                    org.is_active ? 'text-amber-600 bg-amber-50 hover:bg-amber-100' : 'text-green-600 bg-green-50 hover:bg-green-100'
                  ]">
                    {{ org.is_active ? 'Disable' : 'Enable' }}
                  </button>
                  <button @click="openDeleteOrg(org)" class="px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors">
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Reset Password Modal -->
    <Modal :open="showResetModal" title="Reset Password" size="sm" @close="showResetModal = false">
      <div class="space-y-4">
        <div>
          <p class="text-sm text-gray-600">Reset password for <strong>{{ resetOrg?.company_name || resetOrg?.username }}</strong> ({{ resetOrg?.username }})</p>
        </div>
        <div v-if="resetMsg" :class="[
          'rounded-lg px-4 py-3 text-sm border',
          resetMsgType === 'success' ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'
        ]">
          {{ resetMsg }}
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">New Password</label>
          <div class="flex gap-2">
            <input
              v-model="newPassword"
              type="text"
              placeholder="Enter new password"
              class="flex-1 px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary font-mono"
            />
            <button @click="generatePassword" class="px-3 py-2 text-xs font-medium text-primary bg-primary/5 border border-primary/20 rounded-lg hover:bg-primary/10 transition-colors whitespace-nowrap">
              Generate
            </button>
          </div>
        </div>
      </div>
      <template #footer>
        <button @click="showResetModal = false" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
          Close
        </button>
        <button @click="handleResetPassword" :disabled="resetLoading || !newPassword" class="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-lg disabled:opacity-50">
          {{ resetLoading ? 'Resetting...' : 'Reset Password' }}
        </button>
      </template>
    </Modal>

    <!-- Delete Organization Modal -->
    <Modal :open="showDeleteModal" title="Delete Organization" size="sm" @close="showDeleteModal = false">
      <div class="space-y-4">
        <div class="flex items-start gap-3 rounded-lg bg-red-50 border border-red-200 p-4">
          <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>
          <div>
            <p class="text-sm font-medium text-red-800">This action is permanent and cannot be undone.</p>
            <p class="text-sm text-red-700 mt-1">Deleting <strong>{{ deleteOrg?.company_name || deleteOrg?.username }}</strong> will permanently remove their account and all associated data including customers, invoices, payments, routers, and settings.</p>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">
            Type <strong class="font-mono text-red-600">{{ deleteOrg?.username }}</strong> to confirm
          </label>
          <input
            v-model="deleteConfirmText"
            type="text"
            placeholder="Enter username to confirm"
            class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-red-300 focus:border-red-400"
          />
        </div>
      </div>
      <template #footer>
        <button @click="showDeleteModal = false" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
          Cancel
        </button>
        <button
          @click="handleDeleteOrg"
          :disabled="deleteLoading || deleteConfirmText !== deleteOrg?.username"
          class="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {{ deleteLoading ? 'Deleting...' : 'Delete Organization' }}
        </button>
      </template>
    </Modal>
  </div>
</template>
