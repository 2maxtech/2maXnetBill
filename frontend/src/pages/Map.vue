<script setup lang="ts">
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Network Map</h1>
      <p class="text-sm text-gray-500 mt-1">Visualize customer locations and network infrastructure</p>
    </div>

    <!-- Placeholder Card -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-12">
      <div class="flex flex-col items-center justify-center text-center">
        <div class="w-20 h-20 rounded-2xl bg-orange-50 flex items-center justify-center mb-6">
          <svg class="w-10 h-10 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0116 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
        </div>
        <h2 class="text-lg font-semibold text-gray-900 mb-2">Coming Soon</h2>
        <p class="text-sm text-gray-500 max-w-md">
          Customer map visualization coming soon. This feature will display customer locations on an interactive map.
        </p>
      </div>
    </div>
  </div>
</template>
