<script setup lang="ts">
defineProps<{
  status: string
}>()

const statusColors: Record<string, { dot: string; text: string; bg: string }> = {
  active: { dot: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' },
  online: { dot: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' },
  paid: { dot: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' },
  resolved: { dot: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' },
  sent: { dot: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' },
  unused: { dot: 'bg-blue-500', text: 'text-blue-700', bg: 'bg-blue-50' },
  open: { dot: 'bg-blue-500', text: 'text-blue-700', bg: 'bg-blue-50' },
  suspended: { dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50' },
  overdue: { dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50' },
  pending: { dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50' },
  in_progress: { dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50' },
  expired: { dot: 'bg-gray-400', text: 'text-gray-600', bg: 'bg-gray-50' },
  disconnected: { dot: 'bg-red-500', text: 'text-red-700', bg: 'bg-red-50' },
  terminated: { dot: 'bg-gray-400', text: 'text-gray-600', bg: 'bg-gray-50' },
  void: { dot: 'bg-gray-400', text: 'text-gray-600', bg: 'bg-gray-50' },
  closed: { dot: 'bg-gray-400', text: 'text-gray-600', bg: 'bg-gray-50' },
  failed: { dot: 'bg-red-500', text: 'text-red-700', bg: 'bg-red-50' },
  revoked: { dot: 'bg-red-500', text: 'text-red-700', bg: 'bg-red-50' },
  critical: { dot: 'bg-red-500', text: 'text-red-700', bg: 'bg-red-50' },
  high: { dot: 'bg-orange-500', text: 'text-orange-700', bg: 'bg-orange-50' },
  medium: { dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50' },
  low: { dot: 'bg-blue-500', text: 'text-blue-700', bg: 'bg-blue-50' },
  partial: { dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50' },
  inactive: { dot: 'bg-gray-400', text: 'text-gray-600', bg: 'bg-gray-50' },
}

function getColor(status: string) {
  return statusColors[status] || { dot: 'bg-gray-400', text: 'text-gray-600', bg: 'bg-gray-50' }
}
</script>

<template>
  <span :class="['inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium', getColor(status).bg, getColor(status).text]">
    <span :class="['w-1.5 h-1.5 rounded-full', getColor(status).dot]" />
    {{ status.replace(/_/g, ' ') }}
  </span>
</template>
