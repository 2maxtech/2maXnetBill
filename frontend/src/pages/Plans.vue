<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPlans, createPlan, updatePlan, deletePlan, type Plan } from '../api/plans'
import StatusBadge from '../components/common/StatusBadge.vue'
import Modal from '../components/common/Modal.vue'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import SkeletonTable from '../components/SkeletonTable.vue'
import EmptyState from '../components/EmptyState.vue'

const plans = ref<Plan[]>([])
const loading = ref(false)

// Modal
const showModal = ref(false)
const editingPlan = ref<Plan | null>(null)
const saving = ref(false)

const form = ref({
  name: '',
  download_mbps: '',
  upload_mbps: '',
  monthly_price: '',
  data_cap_gb: '',
  fup_download_mbps: '',
  fup_upload_mbps: '',
  local_address: '',
  remote_address: '',
  dns_server: '',
  parent_queue: '',
  description: '',
  is_active: true,
})

// Delete confirm
const showDeleteConfirm = ref(false)
const deleteTarget = ref<Plan | null>(null)
const deleteLoading = ref(false)

async function fetchPlans() {
  loading.value = true
  try {
    const { data } = await getPlans()
    plans.value = data
  } catch (e) {
    console.error('Failed to fetch plans', e)
  } finally {
    loading.value = false
  }
}

function openAddModal() {
  editingPlan.value = null
  form.value = {
    name: '',
    download_mbps: '',
    upload_mbps: '',
    monthly_price: '',
    data_cap_gb: '',
    fup_download_mbps: '',
    fup_upload_mbps: '',
    local_address: '',
    remote_address: '',
    dns_server: '',
    parent_queue: '',
    description: '',
    is_active: true,
  }
  showModal.value = true
}

function openEditModal(plan: Plan) {
  editingPlan.value = plan
  form.value = {
    name: plan.name,
    download_mbps: String(plan.download_mbps),
    upload_mbps: String(plan.upload_mbps),
    monthly_price: String(plan.monthly_price),
    data_cap_gb: plan.data_cap_gb != null ? String(plan.data_cap_gb) : '',
    fup_download_mbps: plan.fup_download_mbps != null ? String(plan.fup_download_mbps) : '',
    fup_upload_mbps: plan.fup_upload_mbps != null ? String(plan.fup_upload_mbps) : '',
    local_address: plan.local_address || '',
    remote_address: plan.remote_address || '',
    dns_server: plan.dns_server || '',
    parent_queue: plan.parent_queue || '',
    description: plan.description || '',
    is_active: plan.is_active,
  }
  showModal.value = true
}

async function handleSave() {
  if (!form.value.name || !form.value.download_mbps || !form.value.upload_mbps || !form.value.monthly_price) return
  saving.value = true
  try {
    const payload: Record<string, any> = {
      name: form.value.name,
      download_mbps: parseFloat(form.value.download_mbps),
      upload_mbps: parseFloat(form.value.upload_mbps),
      monthly_price: parseFloat(form.value.monthly_price),
      is_active: form.value.is_active,
      description: form.value.description || null,
      data_cap_gb: form.value.data_cap_gb ? parseFloat(form.value.data_cap_gb) : null,
      fup_download_mbps: form.value.fup_download_mbps ? parseFloat(form.value.fup_download_mbps) : null,
      fup_upload_mbps: form.value.fup_upload_mbps ? parseFloat(form.value.fup_upload_mbps) : null,
      local_address: form.value.local_address || null,
      remote_address: form.value.remote_address || null,
      dns_server: form.value.dns_server || null,
      parent_queue: form.value.parent_queue || null,
    }

    if (editingPlan.value) {
      await updatePlan(editingPlan.value.id, payload)
    } else {
      await createPlan(payload)
    }
    showModal.value = false
    fetchPlans()
  } catch (e) {
    console.error('Save plan failed', e)
  } finally {
    saving.value = false
  }
}

function openDeleteConfirm(plan: Plan) {
  deleteTarget.value = plan
  showDeleteConfirm.value = true
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleteLoading.value = true
  try {
    await deletePlan(deleteTarget.value.id)
    showDeleteConfirm.value = false
    deleteTarget.value = null
    fetchPlans()
  } catch (e) {
    console.error('Delete plan failed', e)
  } finally {
    deleteLoading.value = false
  }
}

function formatCurrency(val: number | string) {
  return '₱' + Number(val).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

onMounted(fetchPlans)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <h1 class="text-2xl font-bold text-gray-900">Service Plans</h1>
      <button
        @click="openAddModal"
        class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors"
      >
        Add Plan
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Name</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Download</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Upload</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Price</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Data Cap</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Status</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <!-- Loading -->
            <template v-if="loading">
              <tr><td :colspan="7" class="p-0"><SkeletonTable :cols="7" :rows="5" /></td></tr>
            </template>
            <!-- Empty -->
            <tr v-else-if="!plans.length">
              <td colspan="7">
                <EmptyState
                  icon="layers"
                  title="No plans created"
                  description="Create bandwidth plans with pricing that map to MikroTik PPPoE profiles."
                  :actions="[{ label: 'Create Plan', to: '#', primary: true }]"
                  @action="openAddModal"
                />
              </td>
            </tr>
            <!-- Rows -->
            <tr v-else v-for="plan in plans" :key="plan.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-4 py-3 text-sm text-gray-800 font-medium">{{ plan.name }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ plan.download_mbps }} <span class="text-gray-400">Mbps</span></td>
              <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ plan.upload_mbps }} <span class="text-gray-400">Mbps</span></td>
              <td class="px-4 py-3 text-sm text-gray-700 text-right font-medium">{{ formatCurrency(plan.monthly_price) }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 text-right">
                <span v-if="plan.data_cap_gb != null">{{ plan.data_cap_gb }} GB</span>
                <span v-else class="text-gray-400">Unlimited</span>
              </td>
              <td class="px-4 py-3 text-center">
                <StatusBadge :status="plan.is_active ? 'active' : 'inactive'" />
              </td>
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-1">
                  <button
                    @click="openEditModal(plan)"
                    title="Edit plan"
                    class="p-1.5 rounded-lg text-gray-400 hover:text-primary hover:bg-orange-50 transition-colors"
                  >
                    <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
                  </button>
                  <button
                    @click="openDeleteConfirm(plan)"
                    title="Delete plan"
                    class="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <Modal :open="showModal" :title="editingPlan ? 'Edit Plan' : 'Add Plan'" size="lg" @close="showModal = false">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <!-- Name -->
        <div class="sm:col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Plan Name</label>
          <input
            v-model="form.name"
            type="text"
            placeholder="e.g. Fiber 50"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <!-- Download -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Download (Mbps)</label>
          <input
            v-model="form.download_mbps"
            type="number"
            step="1"
            min="0"
            placeholder="50"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <!-- Upload -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Upload (Mbps)</label>
          <input
            v-model="form.upload_mbps"
            type="number"
            step="1"
            min="0"
            placeholder="25"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <!-- Monthly Price -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Monthly Price (₱)</label>
          <input
            v-model="form.monthly_price"
            type="number"
            step="0.01"
            min="0"
            placeholder="1500.00"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <!-- Data Cap -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Data Cap (GB) <span class="text-gray-400 font-normal">- leave blank for unlimited</span></label>
          <input
            v-model="form.data_cap_gb"
            type="number"
            step="1"
            min="0"
            placeholder="Unlimited"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <!-- FUP Download -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">FUP Download (Mbps) <span class="text-gray-400 font-normal">- optional</span></label>
          <input
            v-model="form.fup_download_mbps"
            type="number"
            step="1"
            min="0"
            placeholder="10"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <!-- FUP Upload -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">FUP Upload (Mbps) <span class="text-gray-400 font-normal">- optional</span></label>
          <input
            v-model="form.fup_upload_mbps"
            type="number"
            step="1"
            min="0"
            placeholder="5"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <!-- MikroTik Profile Settings -->
        <div class="sm:col-span-2 border-t border-gray-100 pt-4 mt-2">
          <h4 class="text-sm font-semibold text-gray-800 mb-3">MikroTik Profile Settings <span class="text-gray-400 font-normal">- optional</span></h4>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Local Address</label>
          <input
            v-model="form.local_address"
            type="text"
            placeholder="192.168.50.1"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Remote Address (IP Pool)</label>
          <input
            v-model="form.remote_address"
            type="text"
            placeholder="pppoe-pool"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">DNS Server</label>
          <input
            v-model="form.dns_server"
            type="text"
            placeholder="8.8.8.8,1.1.1.1"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Parent Queue</label>
          <input
            v-model="form.parent_queue"
            type="text"
            placeholder="none"
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>

        <!-- Description -->
        <div class="sm:col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
          <textarea
            v-model="form.description"
            rows="3"
            placeholder="Plan description..."
            class="w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors resize-none"
          />
        </div>

        <!-- Active toggle (edit only) -->
        <div v-if="editingPlan" class="sm:col-span-2">
          <label class="flex items-center gap-3 cursor-pointer">
            <button
              type="button"
              @click="form.is_active = !form.is_active"
              :class="[
                'relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary/30',
                form.is_active ? 'bg-primary' : 'bg-gray-200'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition duration-200 ease-in-out',
                  form.is_active ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
            <span class="text-sm font-medium text-gray-700">{{ form.is_active ? 'Active' : 'Inactive' }}</span>
          </label>
        </div>
      </div>
      <template #footer>
        <button
          @click="showModal = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="handleSave"
          :disabled="!form.name || !form.download_mbps || !form.upload_mbps || !form.monthly_price || saving"
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ saving ? 'Saving...' : (editingPlan ? 'Update Plan' : 'Create Plan') }}
        </button>
      </template>
    </Modal>

    <!-- Delete Confirm -->
    <ConfirmDialog
      :open="showDeleteConfirm"
      title="Delete Plan"
      :message="`Are you sure you want to delete the plan '${deleteTarget?.name}'? This cannot be undone.`"
      confirm-text="Delete Plan"
      :danger="true"
      :loading="deleteLoading"
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false; deleteTarget = null"
    />
  </div>
</template>
