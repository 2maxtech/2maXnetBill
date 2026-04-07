<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getNetworkStatus, type NetworkStatus } from '../../api/network'

const mikrotik = ref<NetworkStatus | null>(null)
const mikrotikLoading = ref(true)
const mikrotikError = ref(false)

async function fetchMikrotikStatus() {
  mikrotikLoading.value = true
  mikrotikError.value = false
  try {
    const { data } = await getNetworkStatus()
    mikrotik.value = data
  } catch (e) {
    mikrotikError.value = true
  } finally {
    mikrotikLoading.value = false
  }
}

onMounted(fetchMikrotikStatus)
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">System Status</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Database -->
      <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center">
            <svg class="w-6 h-6 text-green-600" viewBox="0 0 20 20" fill="currentColor">
              <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z" />
              <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z" />
              <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z" />
            </svg>
          </div>
          <div>
            <h3 class="text-sm font-medium text-gray-500">Database</h3>
            <p class="text-lg font-semibold text-gray-900">PostgreSQL</p>
            <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 mt-1">
              <span class="w-1.5 h-1.5 rounded-full bg-green-500" />
              Connected
            </span>
          </div>
        </div>
      </div>

      <!-- Redis -->
      <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-lg bg-red-100 flex items-center justify-center">
            <svg class="w-6 h-6 text-red-600" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm14 1a1 1 0 11-2 0 1 1 0 012 0zM2 13a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H4a2 2 0 01-2-2v-2zm14 1a1 1 0 11-2 0 1 1 0 012 0z" clip-rule="evenodd" />
            </svg>
          </div>
          <div>
            <h3 class="text-sm font-medium text-gray-500">Redis</h3>
            <p class="text-lg font-semibold text-gray-900">Cache Store</p>
            <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 mt-1">
              <span class="w-1.5 h-1.5 rounded-full bg-green-500" />
              Connected
            </span>
          </div>
        </div>
      </div>

      <!-- Backend API -->
      <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
            <svg class="w-6 h-6 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </div>
          <div>
            <h3 class="text-sm font-medium text-gray-500">Backend API</h3>
            <p class="text-lg font-semibold text-gray-900">FastAPI</p>
            <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 mt-1">
              <span class="w-1.5 h-1.5 rounded-full bg-green-500" />
              Running
            </span>
          </div>
        </div>
      </div>

      <!-- MikroTik -->
      <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
        <div class="flex items-center gap-4">
          <div :class="[
            'w-12 h-12 rounded-lg flex items-center justify-center',
            mikrotikError ? 'bg-red-100' : 'bg-orange-100'
          ]">
            <svg :class="['w-6 h-6', mikrotikError ? 'text-red-600' : 'text-orange-600']" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.05 3.636a1 1 0 010 1.414 7 7 0 000 9.9 1 1 0 11-1.414 1.414 9 9 0 010-12.728 1 1 0 011.414 0zm9.9 0a9 9 0 010 12.728 1 1 0 11-1.414-1.414 7 7 0 000-9.9 1 1 0 011.414-1.414zM7.879 6.464a1 1 0 010 1.414 3 3 0 000 4.243 1 1 0 01-1.415 1.414 5 5 0 010-7.07 1 1 0 011.415 0zm4.242 0a5 5 0 010 7.072 1 1 0 01-1.415-1.415 3 3 0 000-4.242 1 1 0 011.415-1.415zM10 9a1 1 0 011 1v.01a1 1 0 11-2 0V10a1 1 0 011-1z" clip-rule="evenodd" />
            </svg>
          </div>
          <div>
            <h3 class="text-sm font-medium text-gray-500">MikroTik Router</h3>
            <template v-if="mikrotikLoading">
              <div class="h-5 w-32 bg-gray-100 rounded animate-pulse mt-1" />
              <div class="h-5 w-20 bg-gray-100 rounded animate-pulse mt-2" />
            </template>
            <template v-else-if="mikrotikError || !mikrotik?.connected">
              <p class="text-lg font-semibold text-gray-900">Unreachable</p>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700 mt-1">
                <span class="w-1.5 h-1.5 rounded-full bg-red-500" />
                Disconnected
              </span>
            </template>
            <template v-else>
              <p class="text-lg font-semibold text-gray-900">{{ mikrotik.identity }}</p>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 mt-1">
                <span class="w-1.5 h-1.5 rounded-full bg-green-500" />
                Connected
              </span>
              <div class="mt-3 space-y-1 text-sm text-gray-500">
                <p>Uptime: <span class="text-gray-700">{{ mikrotik.uptime }}</span></p>
                <p>CPU: <span class="text-gray-700">{{ mikrotik.cpu_load }}%</span></p>
                <p>Memory: <span class="text-gray-700">{{ mikrotik.total_memory ? Math.round((mikrotik.total_memory - mikrotik.free_memory) / mikrotik.total_memory * 100) : 0 }}% used</span></p>
              </div>
            </template>
          </div>
        </div>
        <button
          v-if="!mikrotikLoading"
          @click="fetchMikrotikStatus"
          class="mt-4 text-sm text-primary hover:text-primary-hover transition-colors"
        >
          Refresh Status
        </button>
      </div>
    </div>
  </div>
</template>
