import api from './client'

export interface Plan {
  id: string
  name: string
  download_mbps: number
  upload_mbps: number
  monthly_price: number | string
  description: string | null
  is_active: boolean
  data_cap_gb: number | null
  fup_download_mbps: number | null
  fup_upload_mbps: number | null
  local_address: string | null
  remote_address: string | null
  dns_server: string | null
  parent_queue: string | null
  created_at: string
}

export function getPlans(params?: { active_only?: boolean }) {
  return api.get<Plan[]>('/plans/', { params })
}

export function getPlan(id: string) {
  return api.get<Plan>(`/plans/${id}`)
}

export function createPlan(data: Partial<Plan>) {
  return api.post<Plan>('/plans/', data)
}

export function updatePlan(id: string, data: Partial<Plan>) {
  return api.put<Plan>(`/plans/${id}`, data)
}

export function deletePlan(id: string) {
  return api.delete(`/plans/${id}`)
}
