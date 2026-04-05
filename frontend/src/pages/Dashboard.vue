<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { getDashboard, type DashboardData } from '../api/network'
import { getRouters, getRouterStatus, type RouterType, type RouterStatus } from '../api/routers'
import StatCard from '../components/common/StatCard.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const data = ref<DashboardData | null>(null)
const loading = ref(true)
const error = ref('')

// Multi-router state
const routers = ref<RouterType[]>([])
const routerStatuses = ref<Map<string, RouterStatus & { interfaces?: any[] }>>(new Map())

let interval: ReturnType<typeof setInterval> | null = null

async function fetchRouters() {
  try {
    const { data: list } = await getRouters()
    routers.value = list.filter(r => r.is_active)
    // Fetch status for each router in parallel
    const statusPromises = routers.value.map(async (r) => {
      try {
        const { data: st } = await getRouterStatus(r.id)
        routerStatuses.value.set(r.id, st)
      } catch {
        routerStatuses.value.set(r.id, { id: r.id, name: r.name, connected: false, error: 'Failed to connect' })
      }
    })
    await Promise.all(statusPromises)
  } catch {
    // No routers in DB — that's fine, we still have the default from dashboard
  }
}

async function fetchDashboard() {
  try {
    const [dashRes] = await Promise.all([getDashboard(), fetchRouters()])
    data.value = dashRes.data
    error.value = ''
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to load dashboard data.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboard()
  interval = setInterval(fetchDashboard, 5000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})

// Determine what to show: DB routers if any, otherwise default MikroTik from dashboard
const showDbRouters = computed(() => routers.value.length > 0)

function fmt(n: number | undefined): string {
  if (n == null) return '0'
  return n.toLocaleString()
}

function peso(n: number | undefined): string {
  if (n == null) return '\u20B10'
  return '\u20B1' + n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function memPercent(free: number | undefined, total: number | undefined): number {
  if (!total) return 0
  return Math.round(((total - (free || 0)) / total) * 100)
}

function formatBytes(bytes: number | undefined): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let val = bytes
  while (val >= 1024 && i < units.length - 1) {
    val /= 1024
    i++
  }
  return val.toFixed(i > 1 ? 2 : 0) + ' ' + units[i]
}

function cpuColor(load: number | string | undefined): string {
  const n = Number(load) || 0
  if (n > 80) return 'text-red-600'
  if (n > 50) return 'text-amber-600'
  return 'text-green-600'
}

function cpuBarColor(load: number | string | undefined): string {
  const n = Number(load) || 0
  if (n > 80) return 'bg-red-500'
  if (n > 50) return 'bg-amber-500'
  return 'bg-green-500'
}

function memColor(free: number | undefined, total: number | undefined): string {
  const p = memPercent(free, total)
  if (p > 80) return 'text-red-600'
  if (p > 50) return 'text-amber-600'
  return 'text-green-600'
}

function memBarColor(free: number | undefined, total: number | undefined): string {
  const p = memPercent(free, total)
  if (p > 80) return 'bg-red-500'
  if (p > 50) return 'bg-amber-500'
  return 'bg-green-500'
}

// Chart config
const chartData = computed(() => {
  const trend = data.value?.revenue_trend || []
  return {
    labels: trend.map((r) => r.month),
    datasets: [
      {
        label: 'Collected',
        backgroundColor: '#e8700a',
        borderRadius: 4,
        data: trend.map((r) => r.collected),
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: { usePointStyle: true, pointStyle: 'circle', padding: 20, font: { family: 'Inter', size: 12 } },
    },
    tooltip: {
      callbacks: {
        label: (ctx: any) => `${ctx.dataset.label}: \u20B1${ctx.raw?.toLocaleString() || 0}`,
      },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { family: 'Inter', size: 11 } } },
    y: {
      grid: { color: '#f3f4f6' },
      ticks: { font: { family: 'Inter', size: 11 }, callback: (v: any) => `\u20B1${(v / 1000).toFixed(0)}k` },
    },
  },
}

function formatDate(s: string): string {
  if (!s) return ''
  const d = new Date(s)
  return d.toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="text-sm text-gray-500 mt-0.5">Real-time overview of your ISP operations</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <div v-else-if="error && !data" class="rounded-xl bg-red-50 border border-red-200 p-6 text-center">
      <p class="text-red-700 text-sm">{{ error }}</p>
      <button @click="fetchDashboard" class="mt-3 text-sm font-medium text-primary hover:underline">Retry</button>
    </div>

    <template v-else-if="data">
      <!-- Subscriber Stats -->
      <section>
        <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Subscribers</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Total Subscribers" :value="fmt(data.subscribers.total)" color="orange">
            <template #icon>
              <svg class="w-5 h-5 text-orange-600" viewBox="0 0 20 20" fill="currentColor"><path d="M7 8a3 3 0 100-6 3 3 0 000 6zM14.5 9a2.5 2.5 0 100-5 2.5 2.5 0 000 5zM1.615 16.428a1.224 1.224 0 01-.569-1.175 6.002 6.002 0 0111.908 0c.058.467-.172.92-.57 1.174A9.953 9.953 0 017 18a9.953 9.953 0 01-5.385-1.572zM14.5 16h-.106c.07-.297.088-.611.048-.933a7.47 7.47 0 00-1.588-3.755 4.502 4.502 0 015.874 2.636.818.818 0 01-.36.98A7.465 7.465 0 0114.5 16z"/></svg>
            </template>
          </StatCard>
          <StatCard title="Active" :value="fmt(data.subscribers.active)" color="green">
            <template #icon>
              <svg class="w-5 h-5 text-green-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>
            </template>
          </StatCard>
          <StatCard title="Suspended" :value="fmt(data.subscribers.suspended)" color="amber">
            <template #icon>
              <svg class="w-5 h-5 text-amber-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>
            </template>
          </StatCard>
          <StatCard title="PPPoE Online" :value="fmt(data.mikrotik.active_sessions)" color="blue">
            <template #icon>
              <svg class="w-5 h-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M.676 6.941A12.964 12.964 0 0110 4c3.456 0 6.626 1.35 8.964 3.555a.75.75 0 01-1.028 1.09A11.466 11.466 0 0010 5.5c-2.92 0-5.617 1.089-7.66 2.888a.75.75 0 11-.988-1.13l.324.283-.324-.283zm2.594 2.833A9.463 9.463 0 0110 7.5c2.58 0 4.92 1.02 6.639 2.686a.75.75 0 11-1.03 1.09A7.96 7.96 0 0010 9a7.96 7.96 0 00-5.608 2.276.75.75 0 11-1.054-1.068l-.068.066.068-.066V9.84l.932-.066zm2.471 2.56A5.96 5.96 0 0110 11c1.588 0 3.04.616 4.118 1.621a.75.75 0 01-1.012 1.107A4.462 4.462 0 0010 12.5a4.46 4.46 0 00-3.106 1.228.75.75 0 11-1.044-1.078l-.109.116.11-.116v-.066l-.001.066zm2.478 2.463a1.75 1.75 0 113.22.862 1.75 1.75 0 01-3.22-.862z" clip-rule="evenodd"/></svg>
            </template>
          </StatCard>
        </div>
      </section>

      <!-- Revenue Stats -->
      <section>
        <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Revenue</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Monthly Recurring" :value="peso(data.billing.mrr)" color="green">
            <template #icon><svg class="w-5 h-5 text-green-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.577 4.878a.75.75 0 01.919-.53l4.78 1.281a.75.75 0 01.531.919l-1.281 4.78a.75.75 0 01-1.449-.388l.81-3.022a19.407 19.407 0 00-5.594 5.203.75.75 0 01-1.139.093L7 10.06l-4.72 4.72a.75.75 0 01-1.06-1.06l5.25-5.25a.75.75 0 011.06 0l3.024 3.024a20.923 20.923 0 015.545-4.927l-3.042.815a.75.75 0 01-.919-.53l.44.005-.44-.005z" clip-rule="evenodd"/></svg></template>
          </StatCard>
          <StatCard title="Collected This Month" :value="peso(data.billing.collected_this_month)" color="blue">
            <template #icon><svg class="w-5 h-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M1 4a1 1 0 011-1h16a1 1 0 011 1v8a1 1 0 01-1 1H2a1 1 0 01-1-1V4zm12 4a3 3 0 11-6 0 3 3 0 016 0zM4 9a1 1 0 100-2 1 1 0 000 2zm13-1a1 1 0 11-2 0 1 1 0 012 0zM1.75 14.5a.75.75 0 000 1.5c4.417 0 8.693.603 12.749 1.73 1.111.309 2.251-.512 2.251-1.696v-.784a.75.75 0 00-1.5 0v.784a.272.272 0 01-.35.25A49.043 49.043 0 001.75 14.5z" clip-rule="evenodd"/></svg></template>
          </StatCard>
          <StatCard title="Billed This Month" :value="peso(data.billing.billed_this_month)" color="purple">
            <template #icon><svg class="w-5 h-5 text-purple-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.5 2A1.5 1.5 0 003 3.5v13A1.5 1.5 0 004.5 18h11a1.5 1.5 0 001.5-1.5V7.621a1.5 1.5 0 00-.44-1.06l-4.12-4.122A1.5 1.5 0 0011.378 2H4.5zm2.25 8.5a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0 3a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5z" clip-rule="evenodd"/></svg></template>
          </StatCard>
          <StatCard title="Overdue" :value="peso(data.billing.overdue_amount)" color="red">
            <template #icon><svg class="w-5 h-5 text-red-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd"/></svg></template>
          </StatCard>
        </div>
      </section>

      <!-- MikroTik Health — Per Router -->
      <section>
        <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          MikroTik Health
          <span v-if="showDbRouters" class="text-gray-400 font-normal normal-case">&middot; {{ routers.length }} router{{ routers.length > 1 ? 's' : '' }}</span>
        </h2>

        <!-- DB Routers: one card per router -->
        <div v-if="showDbRouters" class="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div
            v-for="r in routers"
            :key="r.id"
            class="rounded-xl bg-white shadow-sm border border-gray-100 p-5"
          >
            <!-- Router header -->
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center">
                  <svg class="w-5 h-5 text-gray-600" viewBox="0 0 20 20" fill="currentColor"><path d="M4.632 3.533A2 2 0 016.577 2h6.846a2 2 0 011.945 1.533l1.976 8.234A3.489 3.489 0 0016 11.5H4c-.476 0-.93.095-1.344.267l1.976-8.234z"/><path fill-rule="evenodd" d="M4 13a2 2 0 100 4h12a2 2 0 100-4H4zm11.24 2a.75.75 0 01.75-.75H16a.75.75 0 01.75.75v.01a.75.75 0 01-.75.75h-.01a.75.75 0 01-.75-.75V15zm-2.25-.75a.75.75 0 00-.75.75v.01c0 .414.336.75.75.75H13a.75.75 0 00.75-.75V15a.75.75 0 00-.75-.75h-.01z" clip-rule="evenodd"/></svg>
                </div>
                <div>
                  <p class="font-semibold text-gray-900 text-sm">{{ r.name }}</p>
                  <p class="text-xs text-gray-400">{{ routerStatuses.get(r.id)?.identity || r.url }} <span v-if="routerStatuses.get(r.id)?.version">&middot; v{{ routerStatuses.get(r.id)?.version }}</span></p>
                </div>
              </div>
              <StatusBadge :status="routerStatuses.get(r.id)?.connected ? 'online' : 'disconnected'" />
            </div>

            <template v-if="routerStatuses.get(r.id)?.connected">
              <!-- Stats grid -->
              <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div>
                  <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Uptime</p>
                  <p class="text-sm font-semibold text-gray-900 tabular-nums mt-0.5">{{ routerStatuses.get(r.id)?.uptime || '--' }}</p>
                </div>
                <div>
                  <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Sessions</p>
                  <p class="text-sm font-semibold text-gray-900 tabular-nums mt-0.5">{{ fmt(routerStatuses.get(r.id)?.active_sessions) }}</p>
                </div>
                <!-- CPU -->
                <div>
                  <div class="flex items-center justify-between">
                    <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider">CPU</p>
                    <span class="text-[11px] font-semibold tabular-nums" :class="cpuColor(routerStatuses.get(r.id)?.cpu_load)">{{ routerStatuses.get(r.id)?.cpu_load || 0 }}%</span>
                  </div>
                  <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden mt-1">
                    <div class="h-full rounded-full transition-all duration-500" :class="cpuBarColor(routerStatuses.get(r.id)?.cpu_load)" :style="{ width: (Number(routerStatuses.get(r.id)?.cpu_load) || 0) + '%' }" />
                  </div>
                </div>
                <!-- Memory -->
                <div>
                  <div class="flex items-center justify-between">
                    <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Memory</p>
                    <span class="text-[11px] font-semibold tabular-nums" :class="memColor(routerStatuses.get(r.id)?.free_memory, routerStatuses.get(r.id)?.total_memory)">{{ memPercent(routerStatuses.get(r.id)?.free_memory, routerStatuses.get(r.id)?.total_memory) }}%</span>
                  </div>
                  <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden mt-1">
                    <div class="h-full rounded-full transition-all duration-500" :class="memBarColor(routerStatuses.get(r.id)?.free_memory, routerStatuses.get(r.id)?.total_memory)" :style="{ width: memPercent(routerStatuses.get(r.id)?.free_memory, routerStatuses.get(r.id)?.total_memory) + '%' }" />
                  </div>
                </div>
              </div>

              <!-- Network Activity / Interface Traffic -->
              <div v-if="(data?.mikrotik?.interfaces || []).length > 0 || true" class="border-t border-gray-100 pt-3">
                <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider mb-2">Network Activity</p>
                <div class="space-y-2">
                  <div v-for="iface in (data?.mikrotik?.interfaces || [])" :key="iface.name" class="flex items-center gap-3">
                    <div class="flex items-center gap-1.5 w-24 shrink-0">
                      <span class="w-1.5 h-1.5 rounded-full" :class="iface.running ? 'bg-green-500' : 'bg-gray-300'" />
                      <span class="text-xs font-mono text-gray-600 truncate">{{ iface.name }}</span>
                    </div>
                    <div class="flex-1 grid grid-cols-2 gap-3">
                      <div class="flex items-center gap-1.5">
                        <svg class="w-3 h-3 text-green-500" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 17a.75.75 0 01-.75-.75V5.612L5.29 9.77a.75.75 0 01-1.08-1.04l5.25-5.5a.75.75 0 011.08 0l5.25 5.5a.75.75 0 11-1.08 1.04l-3.96-4.158V16.25A.75.75 0 0110 17z" clip-rule="evenodd"/></svg>
                        <span class="text-xs text-gray-600 tabular-nums">{{ formatBytes(iface.tx_bytes) }}</span>
                      </div>
                      <div class="flex items-center gap-1.5">
                        <svg class="w-3 h-3 text-blue-500" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 3a.75.75 0 01.75.75v10.638l3.96-4.158a.75.75 0 111.08 1.04l-5.25 5.5a.75.75 0 01-1.08 0l-5.25-5.5a.75.75 0 111.08-1.04l3.96 4.158V3.75A.75.75 0 0110 3z" clip-rule="evenodd"/></svg>
                        <span class="text-xs text-gray-600 tabular-nums">{{ formatBytes(iface.rx_bytes) }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-if="!(data?.mikrotik?.interfaces || []).length" class="text-xs text-gray-400">No interface data available</div>
                </div>
              </div>
            </template>
            <div v-else class="text-sm text-gray-400 text-center py-4">
              {{ routerStatuses.get(r.id)?.error || 'Unable to connect' }}
            </div>
          </div>
        </div>

        <!-- Default MikroTik (no DB routers) -->
        <div v-else class="rounded-xl bg-white shadow-sm border border-gray-100 p-5">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center">
                <svg class="w-5 h-5 text-gray-600" viewBox="0 0 20 20" fill="currentColor"><path d="M4.632 3.533A2 2 0 016.577 2h6.846a2 2 0 011.945 1.533l1.976 8.234A3.489 3.489 0 0016 11.5H4c-.476 0-.93.095-1.344.267l1.976-8.234z"/><path fill-rule="evenodd" d="M4 13a2 2 0 100 4h12a2 2 0 100-4H4zm11.24 2a.75.75 0 01.75-.75H16a.75.75 0 01.75.75v.01a.75.75 0 01-.75.75h-.01a.75.75 0 01-.75-.75V15zm-2.25-.75a.75.75 0 00-.75.75v.01c0 .414.336.75.75.75H13a.75.75 0 00.75-.75V15a.75.75 0 00-.75-.75h-.01z" clip-rule="evenodd"/></svg>
              </div>
              <div>
                <p class="font-semibold text-gray-900 text-sm">{{ data.mikrotik.identity || 'MikroTik Router' }}</p>
                <p class="text-xs text-gray-400">{{ data.mikrotik.version ? 'RouterOS v' + data.mikrotik.version : '' }}</p>
              </div>
            </div>
            <StatusBadge :status="data.mikrotik.connected ? 'online' : 'disconnected'" />
          </div>

          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Uptime</p>
              <p class="text-sm font-semibold text-gray-900 tabular-nums mt-0.5">{{ data.mikrotik.uptime || '--' }}</p>
            </div>
            <div>
              <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Sessions</p>
              <p class="text-sm font-semibold text-gray-900 tabular-nums mt-0.5">{{ fmt(data.mikrotik.active_sessions) }}</p>
            </div>
            <div>
              <div class="flex items-center justify-between">
                <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider">CPU</p>
                <span class="text-[11px] font-semibold tabular-nums" :class="cpuColor(data.mikrotik.cpu_load)">{{ data.mikrotik.cpu_load }}%</span>
              </div>
              <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden mt-1">
                <div class="h-full rounded-full transition-all duration-500" :class="cpuBarColor(data.mikrotik.cpu_load)" :style="{ width: Number(data.mikrotik.cpu_load) + '%' }" />
              </div>
            </div>
            <div>
              <div class="flex items-center justify-between">
                <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Memory</p>
                <span class="text-[11px] font-semibold tabular-nums" :class="memColor(data.mikrotik.free_memory, data.mikrotik.total_memory)">{{ memPercent(data.mikrotik.free_memory, data.mikrotik.total_memory) }}%</span>
              </div>
              <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden mt-1">
                <div class="h-full rounded-full transition-all duration-500" :class="memBarColor(data.mikrotik.free_memory, data.mikrotik.total_memory)" :style="{ width: memPercent(data.mikrotik.free_memory, data.mikrotik.total_memory) + '%' }" />
              </div>
            </div>
          </div>

          <!-- Network Activity for default router -->
          <div class="border-t border-gray-100 pt-3">
            <p class="text-[11px] font-medium text-gray-400 uppercase tracking-wider mb-2">Network Activity</p>
            <div class="space-y-2">
              <div v-for="iface in (data.mikrotik.interfaces || [])" :key="iface.name" class="flex items-center gap-3">
                <div class="flex items-center gap-1.5 w-24 shrink-0">
                  <span class="w-1.5 h-1.5 rounded-full" :class="iface.running ? 'bg-green-500' : 'bg-gray-300'" />
                  <span class="text-xs font-mono text-gray-600 truncate">{{ iface.name }}</span>
                </div>
                <div class="flex-1 grid grid-cols-2 gap-3">
                  <div class="flex items-center gap-1.5">
                    <svg class="w-3 h-3 text-green-500" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 17a.75.75 0 01-.75-.75V5.612L5.29 9.77a.75.75 0 01-1.08-1.04l5.25-5.5a.75.75 0 011.08 0l5.25 5.5a.75.75 0 11-1.08 1.04l-3.96-4.158V16.25A.75.75 0 0110 17z" clip-rule="evenodd"/></svg>
                    <span class="text-xs text-gray-600 tabular-nums">TX: {{ formatBytes(iface.tx_bytes) }}</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <svg class="w-3 h-3 text-blue-500" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 3a.75.75 0 01.75.75v10.638l3.96-4.158a.75.75 0 111.08 1.04l-5.25 5.5a.75.75 0 01-1.08 0l-5.25-5.5a.75.75 0 111.08-1.04l3.96 4.158V3.75A.75.75 0 0110 3z" clip-rule="evenodd"/></svg>
                    <span class="text-xs text-gray-600 tabular-nums">RX: {{ formatBytes(iface.rx_bytes) }}</span>
                  </div>
                </div>
              </div>
              <div v-if="!(data.mikrotik.interfaces || []).length" class="text-xs text-gray-400">No interface data available</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Chart + Recent Payments -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
          <h3 class="text-sm font-semibold text-gray-900 mb-4">Revenue Trend</h3>
          <div class="h-64">
            <Bar v-if="data.revenue_trend?.length" :data="chartData" :options="chartOptions" />
            <div v-else class="flex items-center justify-center h-full text-sm text-gray-400">No revenue data</div>
          </div>
        </div>
        <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6">
          <h3 class="text-sm font-semibold text-gray-900 mb-4">Recent Payments</h3>
          <div v-if="data.recent_payments?.length" class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-100">
                  <th class="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                  <th class="text-right py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th class="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Method</th>
                  <th class="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="p in data.recent_payments.slice(0, 5)" :key="p.id" class="hover:bg-gray-50/50 transition-colors">
                  <td class="py-2.5 px-3 font-medium text-gray-900">{{ p.customer_name || '—' }}</td>
                  <td class="py-2.5 px-3 text-right tabular-nums text-gray-900">{{ peso(p.amount) }}</td>
                  <td class="py-2.5 px-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 capitalize">{{ p.method }}</span>
                  </td>
                  <td class="py-2.5 px-3 text-gray-500">{{ formatDate(p.received_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="flex items-center justify-center h-40 text-sm text-gray-400">No recent payments</div>
        </div>
      </section>
    </template>
  </div>
</template>
