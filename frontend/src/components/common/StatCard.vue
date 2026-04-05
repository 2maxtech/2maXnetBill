<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  icon?: string
  color?: 'orange' | 'green' | 'blue' | 'red' | 'amber' | 'purple' | 'cyan'
  trend?: { value: number; label?: string }
}>()

const colorMap: Record<string, { bg: string; text: string; border: string }> = {
  orange: { bg: 'bg-orange-100', text: 'text-orange-600', border: 'border-l-orange-500' },
  green: { bg: 'bg-green-100', text: 'text-green-600', border: 'border-l-green-500' },
  blue: { bg: 'bg-blue-100', text: 'text-blue-600', border: 'border-l-blue-500' },
  red: { bg: 'bg-red-100', text: 'text-red-600', border: 'border-l-red-500' },
  amber: { bg: 'bg-amber-100', text: 'text-amber-600', border: 'border-l-amber-500' },
  purple: { bg: 'bg-purple-100', text: 'text-purple-600', border: 'border-l-purple-500' },
  cyan: { bg: 'bg-cyan-100', text: 'text-cyan-600', border: 'border-l-cyan-500' },
}
</script>

<template>
  <div :class="[
    'rounded-xl bg-white shadow-sm border border-gray-100 p-5 hover:-translate-y-0.5 hover:shadow-md transition-all duration-200',
    color ? `border-l-4 ${colorMap[color]?.border}` : ''
  ]">
    <div class="flex items-start justify-between">
      <div>
        <p class="text-xs font-medium text-gray-500 uppercase tracking-wider">{{ title }}</p>
        <p class="text-2xl font-bold text-gray-900 mt-1 tabular-nums">{{ value }}</p>
        <p v-if="trend" class="text-xs mt-1" :class="trend.value >= 0 ? 'text-green-600' : 'text-red-600'">
          {{ trend.value >= 0 ? '↑' : '↓' }} {{ Math.abs(trend.value) }}% {{ trend.label || '' }}
        </p>
      </div>
      <div v-if="color" :class="['w-10 h-10 rounded-lg flex items-center justify-center', colorMap[color]?.bg]">
        <slot name="icon">
          <span :class="['text-lg', colorMap[color]?.text]">●</span>
        </slot>
      </div>
    </div>
  </div>
</template>
