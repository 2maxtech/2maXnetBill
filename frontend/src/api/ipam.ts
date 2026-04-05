import api from './client'

export interface IPPool {
  id: string
  name: string
  router_id: string | null
  range_start: string
  range_end: string
  subnet: string
  created_at?: string
}

export function getIPPools() {
  return api.get<IPPool[]>('/ipam/pools')
}

export function createIPPool(data: Partial<IPPool>) {
  return api.post<IPPool>('/ipam/pools', data)
}

export function updateIPPool(id: string, data: Partial<IPPool>) {
  return api.put<IPPool>(`/ipam/pools/${id}`, data)
}

export function deleteIPPool(id: string) {
  return api.delete(`/ipam/pools/${id}`)
}
