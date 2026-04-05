<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import dayjs from 'dayjs'
import { getPortalUsage } from '../../api/portal'

const days = ref(7)
const usageData = ref<any[]>([])
const loading = ref(false)

const dayOptions = [7, 14, 30, 60]

function formatBytes(bytes: number) {
  if (!bytes || bytes === 0) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i]
}

function formatSpeed(bps: number) {
  if (!bps || bps === 0) return '-'
  if (bps >= 1_000_000) return (bps / 1_000_000).toFixed(2) + ' Mbps'
  if (bps >= 1_000) return (bps / 1_000).toFixed(2) + ' Kbps'
  return bps + ' bps'
}

async function fetchUsage() {
  loading.value = true
  try {
    const { data } = await getPortalUsage(days.value)
    usageData.value = Array.isArray(data) ? data : data.items || []
  } catch (e) {
    console.error('Failed to fetch usage', e)
    usageData.value = []
  } finally {
    loading.value = false
  }
}

watch(days, fetchUsage)
onMounted(fetchUsage)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <h1 class="text-2xl font-bold text-gray-900">Usage History</h1>
      <div class="flex items-center gap-1 rounded-lg bg-gray-100 p-1">
        <button
          v-for="opt in dayOptions"
          :key="opt"
          @click="days = opt"
          :class="[
            'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
            days === opt
              ? 'bg-white text-primary shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          ]"
        >
          {{ opt }}d
        </button>
      </div>
    </div>

    <!-- Usage Table -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-left">Date</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Download</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Upload</th>
              <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Peak Speed</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <!-- Loading -->
            <template v-if="loading">
              <tr v-for="i in 5" :key="i">
                <td v-for="j in 4" :key="j" class="px-4 py-3">
                  <div class="h-4 bg-gray-100 rounded animate-pulse" />
                </td>
              </tr>
            </template>
            <!-- Empty -->
            <tr v-else-if="!usageData.length">
              <td colspan="4" class="px-4 py-12 text-center text-gray-400">No usage data for this period</td>
            </tr>
            <!-- Rows -->
            <tr v-else v-for="row in usageData" :key="row.date" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-4 py-3 text-sm text-gray-700 font-medium">{{ dayjs(row.date).format('MMM D, YYYY') }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ formatBytes(row.bytes_in) }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ formatBytes(row.bytes_out) }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ formatSpeed(row.peak_speed) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Usage Summary -->
    <div v-if="usageData.length" class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
      <h2 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">Period Summary</h2>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-6">
        <div>
          <p class="text-xs text-gray-500">Total Download</p>
          <p class="text-lg font-bold text-gray-900">
            {{ formatBytes(usageData.reduce((sum: number, r: any) => sum + (r.bytes_in || 0), 0)) }}
          </p>
        </div>
        <div>
          <p class="text-xs text-gray-500">Total Upload</p>
          <p class="text-lg font-bold text-gray-900">
            {{ formatBytes(usageData.reduce((sum: number, r: any) => sum + (r.bytes_out || 0), 0)) }}
          </p>
        </div>
        <div>
          <p class="text-xs text-gray-500">Days Tracked</p>
          <p class="text-lg font-bold text-gray-900">{{ usageData.length }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
