<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import Modal from '../components/common/Modal.vue'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import { getAreas, createArea, updateArea, deleteArea, getRouters } from '../api/routers'
import type { AreaType, RouterType } from '../api/routers'

const areas = ref<AreaType[]>([])
const routers = ref<RouterType[]>([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)

const showModal = ref(false)
const showDeleteDialog = ref(false)
const editingArea = ref<AreaType | null>(null)
const deletingArea = ref<AreaType | null>(null)

const form = ref({
  name: '',
  description: '',
  router_id: '',
})

async function loadData() {
  loading.value = true
  try {
    const [areasRes, routersRes] = await Promise.all([getAreas(), getRouters()])
    areas.value = areasRes.data
    routers.value = routersRes.data
  } catch (e) {
    console.error('Failed to load areas:', e)
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingArea.value = null
  form.value = { name: '', description: '', router_id: '' }
  showModal.value = true
}

function openEdit(area: AreaType) {
  editingArea.value = area
  form.value = {
    name: area.name,
    description: area.description || '',
    router_id: area.router_id || '',
  }
  showModal.value = true
}

function openDelete(area: AreaType) {
  deletingArea.value = area
  showDeleteDialog.value = true
}

async function handleSave() {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    const payload = {
      name: form.value.name.trim(),
      description: form.value.description.trim() || undefined,
      router_id: form.value.router_id || undefined,
    }
    if (editingArea.value) {
      await updateArea(editingArea.value.id, payload)
    } else {
      await createArea(payload)
    }
    showModal.value = false
    await loadData()
  } catch (e) {
    console.error('Failed to save area:', e)
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!deletingArea.value) return
  deleting.value = true
  try {
    await deleteArea(deletingArea.value.id)
    showDeleteDialog.value = false
    deletingArea.value = null
    await loadData()
  } catch (e) {
    console.error('Failed to delete area:', e)
  } finally {
    deleting.value = false
  }
}

function getRouterName(area: AreaType): string {
  if (area.router?.name) return area.router.name
  if (!area.router_id) return '-'
  const r = routers.value.find((rt) => rt.id === area.router_id)
  return r ? r.name : '-'
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Network Areas</h1>
        <p class="text-sm text-gray-500 mt-1">Manage network service areas and their router assignments</p>
      </div>
      <button
        @click="openAdd"
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary-hover transition-colors"
      >
        <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" />
        </svg>
        Add Area
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Name</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Description</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Router</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Created</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <template v-if="loading">
              <tr v-for="i in 5" :key="i">
                <td v-for="j in 5" :key="j" class="px-4 py-3">
                  <div class="h-4 bg-gray-100 rounded animate-pulse" />
                </td>
              </tr>
            </template>
            <tr v-else-if="!areas.length">
              <td colspan="5" class="px-4 py-12 text-center text-gray-400">No areas found</td>
            </tr>
            <tr v-else v-for="area in areas" :key="area.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ area.name }}</td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ area.description || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700">{{ getRouterName(area) }}</td>
              <td class="px-4 py-3 text-sm text-gray-500">{{ dayjs(area.created_at).format('MMM D, YYYY') }}</td>
              <td class="px-4 py-3 text-sm text-right">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEdit(area)"
                    class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M2.695 14.763l-1.262 3.154a.5.5 0 00.65.65l3.155-1.262a4 4 0 001.343-.885L17.5 5.5a2.121 2.121 0 00-3-3L3.58 13.42a4 4 0 00-.885 1.343z" />
                    </svg>
                    Edit
                  </button>
                  <button
                    @click="openDelete(area)"
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
    <Modal :open="showModal" :title="editingArea ? 'Edit Area' : 'Add Area'" @close="showModal = false">
      <form @submit.prevent="handleSave" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Name</label>
          <input
            v-model="form.name"
            type="text"
            required
            placeholder="e.g. Zone A - Downtown"
            class="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
          <input
            v-model="form.description"
            type="text"
            placeholder="Optional description"
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
          :disabled="saving || !form.name.trim()"
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : editingArea ? 'Update' : 'Create' }}
        </button>
      </template>
    </Modal>

    <!-- Delete Confirm -->
    <ConfirmDialog
      :open="showDeleteDialog"
      title="Delete Area"
      :message="`Are you sure you want to delete '${deletingArea?.name}'? This action cannot be undone.`"
      confirm-text="Delete"
      :danger="true"
      :loading="deleting"
      @confirm="handleDelete"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>
