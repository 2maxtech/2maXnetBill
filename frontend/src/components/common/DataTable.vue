<script setup lang="ts">
import SkeletonTable from '../SkeletonTable.vue'

defineProps<{
  columns: Array<{
    key: string
    label: string
    width?: string
    align?: 'left' | 'center' | 'right'
  }>
  data: any[]
  loading?: boolean
  rowKey?: string
  emptyText?: string
}>()

defineEmits<{
  rowClick: [row: any]
}>()
</script>

<template>
  <div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th
              v-for="col in columns"
              :key="col.key"
              :style="col.width ? { width: col.width } : {}"
              :class="[
                'px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider',
                col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
              ]"
            >
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <!-- Loading -->
          <template v-if="loading">
            <tr><td :colspan="columns.length" class="p-0"><SkeletonTable :cols="columns.length" :rows="5" /></td></tr>
          </template>
          <!-- Empty -->
          <tr v-else-if="!data?.length">
            <td :colspan="columns.length">
              <slot name="empty">
                <div class="px-4 py-12 text-center text-gray-400">
                  {{ emptyText || 'No data' }}
                </div>
              </slot>
            </td>
          </tr>
          <!-- Rows -->
          <tr
            v-else
            v-for="row in data"
            :key="row[rowKey || 'id']"
            @click="$emit('rowClick', row)"
            class="hover:bg-gray-50/50 transition-colors cursor-pointer"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-4 py-3 text-sm text-gray-700',
                col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
              ]"
            >
              <slot :name="col.key" :row="row" :value="row[col.key]">
                {{ row[col.key] }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
