<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth'
import { useImpersonate } from '../../composables/useImpersonate'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const { isLoading, isAuthenticated, init } = useAuth()
const { impersonating, isImpersonating, exitOrg } = useImpersonate()
const router = useRouter()

onMounted(async () => {
  await init()
  if (!isAuthenticated.value) {
    router.push('/login')
  }
})

function handleExit() {
  exitOrg()
  router.push('/dashboard')
}
</script>

<template>
  <div v-if="isLoading" class="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
    <div class="flex flex-col items-center gap-3">
      <div class="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      <span class="text-sm text-gray-500 dark:text-gray-400">Loading...</span>
    </div>
  </div>
  <div v-else class="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
    <Sidebar />
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Impersonation Banner -->
      <div v-if="isImpersonating" class="flex items-center justify-between px-4 py-2 bg-primary text-white text-sm shrink-0">
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd"/></svg>
          <span>Managing: <strong>{{ impersonating?.company_name }}</strong> ({{ impersonating?.username }})</span>
        </div>
        <button @click="handleExit" class="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/20 hover:bg-white/30 text-xs font-medium transition-colors">
          <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.25 5.5a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 00.75-.75v-4a.75.75 0 011.5 0v4A2.25 2.25 0 0112.75 17h-8.5A2.25 2.25 0 012 14.75v-8.5A2.25 2.25 0 014.25 4h5a.75.75 0 010 1.5h-5z" clip-rule="evenodd"/><path fill-rule="evenodd" d="M6.194 12.753a.75.75 0 001.06.053L16.5 4.44v2.81a.75.75 0 001.5 0v-4.5a.75.75 0 00-.75-.75h-4.5a.75.75 0 000 1.5h2.553l-9.056 8.194a.75.75 0 00-.053 1.06z" clip-rule="evenodd"/></svg>
          Exit to Platform
        </button>
      </div>
      <Header />
      <main class="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-900">
        <router-view />
      </main>
    </div>
  </div>
</template>
