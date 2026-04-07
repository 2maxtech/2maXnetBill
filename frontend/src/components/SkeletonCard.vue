<script setup lang="ts">
withDefaults(defineProps<{
  lines?: number
}>(), {
  lines: 3,
})
</script>

<template>
  <div class="rounded-xl bg-white dark:bg-gray-900 shadow-sm border border-gray-100 dark:border-gray-800 p-5 animate-pulse">
    <!-- Title bar -->
    <div class="h-4 w-1/3 bg-gray-200 dark:bg-gray-700 rounded mb-4" />
    <!-- Content lines -->
    <div class="space-y-3">
      <div
        v-for="i in lines"
        :key="i"
        class="h-3 bg-gray-200 dark:bg-gray-700 rounded"
        :style="{ width: (60 + ((i * 23) % 35)) + '%' }"
      />
    </div>
  </div>
</template>
