import client from './client';

export interface VoucherType {
  id: string;
  code: string;
  plan_id: string;
  duration_days: number;
  status: string;
  customer_id: string | null;
  activated_at: string | null;
  expires_at: string | null;
  batch_id: string | null;
  created_at: string;
}

export const getVouchers = (params?: any) =>
  client.get<VoucherType[]>('/vouchers/', { params });
export const generateVouchers = (data: any) =>
  client.post<VoucherType[]>('/vouchers/generate', data);
export const redeemVoucher = (data: any) => client.post('/vouchers/redeem', data);
export const revokeVoucher = (id: string) => client.delete(`/vouchers/${id}`);
