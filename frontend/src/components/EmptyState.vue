<script setup lang="ts">
import { computed } from 'vue'

interface Action {
  label: string
  to?: string
  primary?: boolean
}

const props = defineProps<{
  icon: string
  title: string
  description: string
  actions?: Action[]
}>()

const emit = defineEmits<{
  action: [label: string]
}>()

function handleAction(action: Action) {
  if (action.to === '#' || !action.to) {
    emit('action', action.label)
  }
}
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 px-4">
    <!-- Icon -->
    <div class="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4">
      <!-- people -->
      <svg v-if="icon === 'people'" viewBox="0 0 48 48" fill="currentColor">
        <path d="M24 22c3.31 0 6-2.69 6-6s-2.69-6-6-6-6 2.69-6 6 2.69 6 6 6zm0-10c2.21 0 4 1.79 4 4s-1.79 4-4 4-4-1.79-4-4 1.79-4 4-4zm0 14c-4.42 0-12 2.22-12 6.6V38h24v-5.4c0-4.38-7.58-6.6-12-6.6zm-10 8c.22-1.1 4.56-4.6 10-4.6s9.78 3.5 10 4.6H14zM38 22c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 4c-1.12 0-2.38.18-3.68.52C36.04 28.18 37 30.14 37 32.6V38h9v-4.4c0-3.74-5.58-5.6-8-5.6zM10 22c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm3.68 4.52C12.38 26.18 11.12 26 10 26c-2.42 0-8 1.86-8 5.6V38h9v-5.4c0-2.46.96-4.42 2.68-6.08z" />
      </svg>
      <!-- server -->
      <svg v-else-if="icon === 'server'" viewBox="0 0 48 48" fill="currentColor">
        <path d="M8 8h32v10H8V8zm2 2v6h28v-6H10zm-2 14h32v10H8V24zm2 2v6h28v-6H10zm-2 14h32v-2H8v2zM14 13a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm0 16a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm5-16a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm0 16a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
      </svg>
      <!-- receipt -->
      <svg v-else-if="icon === 'receipt'" viewBox="0 0 48 48" fill="currentColor">
        <path d="M12 6l3 3 3-3 3 3 3-3 3 3 3-3 3 3 3-3v36l-3-3-3 3-3-3-3 3-3-3-3 3-3-3-3 3V6zm4 10v2h16v-2H16zm0 6v2h16v-2H16zm0 6v2h10v-2H16z" />
      </svg>
      <!-- layers -->
      <svg v-else-if="icon === 'layers'" viewBox="0 0 48 48" fill="currentColor">
        <path d="M24 4L4 16l20 12 20-12L24 4zm0 4.36L38.18 16 24 23.64 9.82 16 24 8.36zM4 24l20 12 20-12-4.36-2.62L24 29.64 8.36 21.38 4 24zm0 8l20 12 20-12-4.36-2.62L24 37.64 8.36 29.38 4 32z" />
      </svg>
      <!-- map-pin -->
      <svg v-else-if="icon === 'map-pin'" viewBox="0 0 48 48" fill="currentColor">
        <path d="M24 4C16.27 4 10 10.27 10 18c0 10.5 14 26 14 26s14-15.5 14-26c0-7.73-6.27-14-14-14zm0 4c5.52 0 10 4.48 10 10 0 6.2-6.58 15.4-10 20.18C20.58 33.4 14 24.2 14 18c0-5.52 4.48-10 10-10zm0 5a5 5 0 100 10 5 5 0 000-10zm0 2a3 3 0 110 6 3 3 0 010-6z" />
      </svg>
      <!-- ticket -->
      <svg v-else-if="icon === 'ticket'" viewBox="0 0 48 48" fill="currentColor">
        <path d="M40 12H8c-2.21 0-4 1.79-4 4v4c2.21 0 4 1.79 4 4s-1.79 4-4 4v4c0 2.21 1.79 4 4 4h32c2.21 0 4-1.79 4-4v-4c-2.21 0-4-1.79-4-4s1.79-4 4-4v-4c0-2.21-1.79-4-4-4zm-2 2c1.1 0 2 .9 2 2v2.54a6.012 6.012 0 00-4 5.46c0 2.38 1.41 4.44 3.44 5.41l.56.05V32c0 1.1-.9 2-2 2H10c-1.1 0-2-.9-2-2v-2.54A6.012 6.012 0 0012 24c0-2.38-1.41-4.44-3.44-5.41L8 18.54V16c0-1.1.9-2 2-2h28zM18 20v2h12v-2H18zm0 6v2h8v-2h-8z" />
      </svg>
      <!-- wifi -->
      <svg v-else-if="icon === 'wifi'" viewBox="0 0 48 48" fill="currentColor">
        <path d="M2.51 16.88C8.18 11.22 15.71 8 24 8s15.82 3.22 21.49 8.88l-2.83 2.83C37.84 14.89 31.22 12 24 12s-13.84 2.89-18.66 7.71L2.51 16.88zM8.17 22.54C12.37 18.34 17.93 16 24 16s11.63 2.34 15.83 6.54l-2.83 2.83C33.48 21.85 28.95 20 24 20s-9.48 1.85-12.99 5.37l-2.84-2.83zM13.85 28.17C16.64 25.39 20.18 24 24 24s7.36 1.39 10.15 4.17l-2.82 2.83C29.25 28.92 26.73 28 24 28s-5.25.92-7.33 3l-2.82-2.83zM24 32a4 4 0 100 8 4 4 0 000-8zm0 2a2 2 0 110 4 2 2 0 010-4z" />
      </svg>
    </div>

    <!-- Title -->
    <h3 class="text-lg font-semibold text-gray-500 dark:text-gray-400 mb-1">{{ title }}</h3>

    <!-- Description -->
    <p class="text-sm text-gray-400 dark:text-gray-500 text-center max-w-sm mb-6">{{ description }}</p>

    <!-- Actions -->
    <div v-if="actions?.length" class="flex items-center gap-3">
      <template v-for="action in actions" :key="action.label">
        <router-link
          v-if="action.to && action.to !== '#'"
          :to="action.to"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            action.primary
              ? 'bg-primary text-white hover:bg-primary-hover'
              : 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
          ]"
        >
          {{ action.label }}
        </router-link>
        <button
          v-else
          @click="handleAction(action)"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            action.primary
              ? 'bg-primary text-white hover:bg-primary-hover'
              : 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
          ]"
        >
          {{ action.label }}
        </button>
      </template>
    </div>
  </div>
</template>
