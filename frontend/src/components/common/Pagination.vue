<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pageSize: number
  total: number
}>()

const emit = defineEmits<{
  'update:page': [page: number]
}>()

const totalPages = computed(() => Math.ceil(props.total / props.pageSize))

const pages = computed(() => {
  const p: (number | '...')[] = []
  const tp = totalPages.value
  const cp = props.page
  if (tp <= 7) {
    for (let i = 1; i <= tp; i++) p.push(i)
  } else {
    p.push(1)
    if (cp > 3) p.push('...')
    for (let i = Math.max(2, cp - 1); i <= Math.min(tp - 1, cp + 1); i++) p.push(i)
    if (cp < tp - 2) p.push('...')
    p.push(tp)
  }
  return p
})
</script>

<template>
  <div class="flex items-center justify-between px-4 py-3">
    <span class="text-sm text-gray-500">{{ total }} total</span>
    <div class="flex items-center gap-1">
      <button
        @click="emit('update:page', page - 1)"
        :disabled="page <= 1"
        class="px-2 py-1 rounded-lg text-sm text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        ← Prev
      </button>
      <template v-for="p in pages" :key="p">
        <span v-if="p === '...'" class="px-2 text-gray-400">...</span>
        <button
          v-else
          @click="emit('update:page', p)"
          :class="[
            'w-8 h-8 rounded-lg text-sm font-medium transition-colors',
            p === page ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          {{ p }}
        </button>
      </template>
      <button
        @click="emit('update:page', page + 1)"
        :disabled="page >= totalPages"
        class="px-2 py-1 rounded-lg text-sm text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Next →
      </button>
    </div>
  </div>
</template>
