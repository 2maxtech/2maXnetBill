import api from './client'

export interface VoucherType {
  id: string
  code: string
  plan_id: string
  duration_days: number
  status: string
  customer_id: string | null
  activated_at: string | null
  expires_at: string | null
  batch_id: string | null
  created_at: string
}

export function getVouchers(params?: { status?: string; batch_id?: string; page?: number; size?: number }) {
  return api.get<{ items: VoucherType[]; total: number }>('/vouchers/', { params })
}

export function generateVouchers(data: { count: number; plan_id: string; duration_days: number }) {
  return api.post<VoucherType[]>('/vouchers/generate', data)
}

export function redeemVoucher(data: { code: string; customer_id: string }) {
  return api.post('/vouchers/redeem', data)
}

export function revokeVoucher(id: string) {
  return api.delete(`/vouchers/${id}`)
}
