<script setup lang="ts">
import Modal from './Modal.vue'

defineProps<{
  open: boolean
  title: string
  message: string
  confirmText?: string
  danger?: boolean
  loading?: boolean
}>()

defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Modal :open="open" :title="title" size="sm" @close="$emit('cancel')">
    <p class="text-sm text-gray-600">{{ message }}</p>
    <template #footer>
      <button
        @click="$emit('cancel')"
        class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
      >
        Cancel
      </button>
      <button
        @click="$emit('confirm')"
        :disabled="loading"
        :class="[
          'px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors disabled:opacity-50',
          danger ? 'bg-red-600 hover:bg-red-700' : 'bg-primary hover:bg-primary-hover'
        ]"
      >
        {{ loading ? 'Processing...' : (confirmText || 'Confirm') }}
      </button>
    </template>
  </Modal>
</template>
