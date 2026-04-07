<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getCustomers, type Customer } from '../api/customers'

const mapContainer = ref<HTMLDivElement>()
const customers = ref<Customer[]>([])
const loading = ref(true)
const hasCoords = ref(false)
let mapInstance: any = null

const statusColors: Record<string, string> = {
  active: '#22c55e',
  suspended: '#f59e0b',
  disconnected: '#ef4444',
  terminated: '#6b7280',
}

const statusLabels: Record<string, string> = {
  active: 'Active',
  suspended: 'Suspended',
  disconnected: 'Disconnected',
  terminated: 'Terminated',
}

function loadLeafletCSS(): Promise<void> {
  return new Promise((resolve) => {
    if (document.querySelector('link[href*="leaflet"]')) {
      resolve()
      return
    }
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    link.onload = () => resolve()
    document.head.appendChild(link)
  })
}

function loadLeafletJS(): Promise<void> {
  return new Promise((resolve) => {
    if ((window as any).L) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.onload = () => resolve()
    document.head.appendChild(script)
  })
}

function createMarkerIcon(color: string) {
  const L = (window as any).L
  return L.divIcon({
    className: '',
    html: `<div style="width:12px;height:12px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
    popupAnchor: [0, -8],
  })
}

async function initMap() {
  loading.value = true
  try {
    // Fetch all customers (up to 10000)
    const { data } = await getCustomers({ page: 1, page_size: 10000 })
    customers.value = data.items

    const withCoords = customers.value.filter(c => c.latitude != null && c.longitude != null)
    hasCoords.value = withCoords.length > 0

    if (!hasCoords.value) {
      loading.value = false
      return
    }

    await loadLeafletCSS()
    await loadLeafletJS()
    await nextTick()

    const L = (window as any).L
    if (!mapContainer.value) return

    mapInstance = L.map(mapContainer.value).setView([12.8797, 121.774], 6)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(mapInstance)

    const bounds: [number, number][] = []

    for (const customer of withCoords) {
      const lat = customer.latitude!
      const lng = customer.longitude!
      const color = statusColors[customer.status] || '#6b7280'
      const label = statusLabels[customer.status] || customer.status

      const marker = L.marker([lat, lng], { icon: createMarkerIcon(color) })
      marker.bindPopup(`
        <div style="min-width:150px">
          <div style="font-weight:600;font-size:14px;margin-bottom:4px">${customer.full_name}</div>
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px">
            <span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block"></span>
            <span style="font-size:12px;color:#666">${label}</span>
          </div>
          ${customer.plan ? `<div style="font-size:12px;color:#666;margin-top:2px">Plan: ${customer.plan.name}</div>` : ''}
          ${customer.address ? `<div style="font-size:11px;color:#999;margin-top:2px">${customer.address}</div>` : ''}
        </div>
      `)
      marker.addTo(mapInstance)
      bounds.push([lat, lng])
    }

    if (bounds.length > 1) {
      mapInstance.fitBounds(bounds, { padding: [30, 30] })
    } else if (bounds.length === 1) {
      mapInstance.setView(bounds[0], 15)
    }
  } catch (e) {
    console.error('Failed to load map', e)
  } finally {
    loading.value = false
  }
}

onMounted(initMap)

onUnmounted(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Network Map</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Visualize customer locations and network infrastructure</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-12">
      <div class="flex flex-col items-center justify-center">
        <div class="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
        <p class="text-sm text-gray-500 dark:text-gray-400">Loading map data...</p>
      </div>
    </div>

    <!-- No coordinates message -->
    <div v-else-if="!hasCoords" class="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-12">
      <div class="flex flex-col items-center justify-center text-center">
        <div class="w-20 h-20 rounded-2xl bg-orange-50 dark:bg-orange-950/30 flex items-center justify-center mb-6">
          <svg class="w-10 h-10 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0116 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
        </div>
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">No Customer Locations</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 max-w-md">
          None of your customers have coordinates set yet. Edit a customer and add their latitude and longitude to see them on the map.
        </p>
      </div>
    </div>

    <!-- Map container -->
    <div v-show="!loading && hasCoords" class="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      <!-- Legend -->
      <div class="flex items-center gap-4 px-4 py-3 border-b border-gray-100 dark:border-gray-700">
        <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</span>
        <div class="flex items-center gap-4">
          <div v-for="(color, status) in statusColors" :key="status" class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded-full" :style="{ background: color }" />
            <span class="text-xs text-gray-600 dark:text-gray-400 capitalize">{{ status }}</span>
          </div>
        </div>
        <span class="ml-auto text-xs text-gray-400 dark:text-gray-500">
          {{ customers.filter(c => c.latitude != null && c.longitude != null).length }} of {{ customers.length }} customers mapped
        </span>
      </div>
      <div ref="mapContainer" style="height: 600px; width: 100%;" />
    </div>
  </div>
</template>
