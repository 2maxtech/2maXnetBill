<script setup lang="ts">
withDefaults(defineProps<{
  cols?: number
  rows?: number
}>(), {
  cols: 5,
  rows: 5,
})
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full">
      <thead>
        <tr class="bg-gray-50 dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700">
          <th v-for="c in cols" :key="c" class="px-4 py-3">
            <div class="h-3 w-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50 dark:divide-gray-800">
        <tr v-for="r in rows" :key="r">
          <td v-for="c in cols" :key="c" class="px-4 py-3">
            <div
              class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
              :style="{ width: (50 + ((r * c * 17) % 40)) + '%' }"
            />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
