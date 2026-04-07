<script setup lang="ts">
import { ref } from 'vue'
import { useAuth } from '../../composables/useAuth'

const { user, logout } = useAuth()
const showMenu = ref(false)
</script>

<template>
  <header class="flex items-center justify-between px-6 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
    <div class="text-lg font-semibold text-gray-800 dark:text-gray-200">
      <slot name="title" />
    </div>
    <div class="relative">
      <button
        @click="showMenu = !showMenu"
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <span class="text-sm font-semibold text-primary">{{ user?.username?.[0]?.toUpperCase() }}</span>
        </div>
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ user?.username }}</span>
        <svg class="w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
      </button>
      <div
        v-if="showMenu"
        @click="showMenu = false"
        class="fixed inset-0 z-40"
      />
      <div
        v-if="showMenu"
        class="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 py-1 z-50"
      >
        <div class="px-4 py-2 border-b border-gray-100 dark:border-gray-700">
          <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ user?.username }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ user?.role }}</p>
        </div>
        <button
          @click="logout()"
          class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
        >
          Sign Out
        </button>
      </div>
    </div>
  </header>
</template>
