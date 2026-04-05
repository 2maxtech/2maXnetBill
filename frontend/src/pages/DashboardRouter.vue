<script setup lang="ts">
import { computed } from 'vue'
import { useAuth } from '../composables/useAuth'
import Dashboard from './Dashboard.vue'
import SuperAdminDashboard from './SuperAdminDashboard.vue'

const { user } = useAuth()
const isSuperAdmin = computed(() => user.value?.role === 'super_admin')
</script>

<template>
  <SuperAdminDashboard v-if="isSuperAdmin" />
  <Dashboard v-else />
</template>
