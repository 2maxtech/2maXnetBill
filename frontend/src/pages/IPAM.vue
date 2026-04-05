<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import Modal from '../components/common/Modal.vue'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import { getIPPools, createIPPool, updateIPPool, deleteIPPool } from '../api/ipam'
import { getRouters } from '../api/routers'
import type { IPPool } from '../api/ipam'
import type { RouterType } from '../api/routers'

const pools = ref<IPPool[]>([])
const routers = ref<RouterType[]>([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)

const showModal = ref(false)
const showDeleteDialog = ref(false)
const editingPool = ref<IPPool | null>(null)
const deletingPool = ref<IPPool | null>(null)

const form = ref({
  name: '',
  router_id: '',
  subnet: '',
  range_start: '',
  range_end: '',
})

async function loadData() {
  loading.value = true
  try {
    const [poolsRes, routersRes] = await Promise.all([getIPPools(), getRouters()])
    pools.value = poolsRes.data
    routers.value = routersRes.data
  } catch (e) {
    console.error('Failed to load IP pools:', e)
  } finally {
    loading.value = false
  }
}

function getRouterName(pool: IPPool): string {
  if (!pool.router_id) return '-'
  const r = routers.value.find((rt) => rt.id === pool.router_id)
  return r ? r.name : '-'
}

function openAdd() {
  editingPool.value = null
  form.value = { name: '', router_id: '', subnet: '', range_start: '', range_end: '' }
  showModal.value = true
}

function openEdit(pool: IPPool) {
  editingPool.value = pool
  form.value = {
    name: pool.name,
    router_id: pool.router_id || '',
    subnet: pool.subnet,
    range_start: pool.range_start,
    range_end: pool.range_end,
  }
  showModal.value = true
}

function openDelete(pool: IPPool) {
  deletingPool.value = pool
  showDeleteDialog.value = true
}

async function handleSave() {
  if (!form.value.name.trim() || !form.value.subnet.trim() || !form.value.range_start.trim() || !form.value.range_end.trim()) return
  saving.value = true
  try {
    const payload: Partial<IPPool> = {
      name: form.value.name.trim(),
      router_id: form.value.router_id || null,
      subnet: form.value.subnet.trim(),
      range_start: form.value.range_start.trim(),
      range_end: form.value.range_end.trim(),
    }
    if (editingPool.value) {
      await updateIPPool(editingPool.value.id, payload)
    } else {
      await createIPPool(payload)
    }
    showModal.value = false
    await loadData()
  } catch (e) {
    console.error('Failed to save IP pool:', e)
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!deletingPool.value) return
  deleting.value = true
  try {
    await deleteIPPool(deletingPool.value.id)
    showDeleteDialog.value = false
    deletingPool.value = null
    await loadData()
  } catch (e) {
    console.error('Failed to delete IP pool:', e)
  } finally {
    deleting.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">IP Address Management</h1>
        <p class="text-sm text-gray-500 mt-1">Manage IP pools and address allocations</p>
      </div>
      <button
        @click="openAdd"
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary-hover transition-colors"
      >
        <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" />
        </svg>
        Add Pool
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Name</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Router</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Subnet</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Range Start</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Range End</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <template v-if="loading">
              <tr v-for="i in 5" :key="i">
                <td v-for="j in 6" :key="j" class="px-4 py-3">
                  <div class="h-4 bg-gray-100 rounded animate-pulse" />
                </td>
              </tr>
            </template>
            <tr v-else-if="!pools.length">
              <td colspan="6" class="px-4 py-12 text-center text-gray-400">No IP pools found</td>
            </tr>
            <tr v-else v-for="pool in pools" :key="pool.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ pool.name }}</td>
              <td class="px-4 py-3 text-sm text-gray-700">{{ getRouterName(pool) }}</td>
              <td class="px-4 py-3 text-sm font-mono text-gray-700">{{ pool.subnet }}</td>
              <td class="px-4 py-3 text-sm font-mono text-gray-600">{{ pool.range_start }}</td>
              <td class="px-4 py-3 text-sm font-mono text-gray-600">{{ pool.range_end }}</td>
              <td class="px-4 py-3 text-sm text-right">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEdit(pool)"
                    class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M2.695 14.763l-1.262 3.154a.5.5 0 00.65.65l3.155-1.262a4 4 0 001.343-.885L17.5 5.5a2.121 2.121 0 00-3-3L3.58 13.42a4 4 0 00-.885 1.343z" />
                    </svg>
                    Edit
                  </button>
                  <button
                    @click="openDelete(pool)"
                    class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                  >
                    <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.519.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clip-rule="evenodd" />
                    </svg>
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <Modal :open="showModal" :title="editingPool ? 'Edit IP Pool' : 'Add IP Pool'" @close="showModal = false">
      <form @submit.prevent="handleSave" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Name</label>
          <input
            v-model="form.name"
            type="text"
            required
            placeholder="e.g. PPPoE Pool 1"
            class="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Router</label>
          <select
            v-model="form.router_id"
            class="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          >
            <option value="">No router assigned</option>
            <option v-for="router in routers" :key="router.id" :value="router.id">{{ router.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Subnet</label>
          <input
            v-model="form.subnet"
            type="text"
            required
            placeholder="e.g. 10.0.0.0/24"
            class="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Range Start</label>
            <input
              v-model="form.range_start"
              type="text"
              required
              placeholder="e.g. 10.0.0.1"
              class="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Range End</label>
            <input
              v-model="form.range_end"
              type="text"
              required
              placeholder="e.g. 10.0.0.254"
              class="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
            />
          </div>
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
          @click="handleSave"
          :disabled="saving || !form.name.trim() || !form.subnet.trim() || !form.range_start.trim() || !form.range_end.trim()"
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : editingPool ? 'Update' : 'Create' }}
        </button>
      </template>
    </Modal>

    <!-- Delete Confirm -->
    <ConfirmDialog
      :open="showDeleteDialog"
      title="Delete IP Pool"
      :message="`Are you sure you want to delete '${deletingPool?.name}'? This action cannot be undone.`"
      confirm-text="Delete"
      :danger="true"
      :loading="deleting"
      @confirm="handleDelete"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>
