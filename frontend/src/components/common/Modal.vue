<script setup lang="ts">
defineProps<{
  open: boolean
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}>()

defineEmits<{
  close: []
}>()

const sizeClasses: Record<string, string> = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')" />
        <div :class="[
          'relative w-full bg-white rounded-xl shadow-2xl',
          sizeClasses[size || 'md']
        ]">
          <div v-if="title" class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <h3 class="text-lg font-semibold text-gray-800">{{ title }}</h3>
            <button @click="$emit('close')" class="p-1 rounded-lg hover:bg-gray-100 transition-colors">
              <svg class="w-5 h-5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="p-6">
            <slot />
          </div>
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active > div:last-child, .modal-leave-active > div:last-child {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
.modal-enter-from > div:last-child {
  transform: scale(0.95);
  opacity: 0;
}
</style>
