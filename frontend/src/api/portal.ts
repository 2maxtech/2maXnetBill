import axios from 'axios';

const portalClient = axios.create({
  baseURL: '/api/v1/portal',
  headers: { 'Content-Type': 'application/json' },
});

portalClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('portal_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

portalClient.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('portal_token');
      localStorage.removeItem('portal_customer');
      window.location.href = '/portal/login';
    }
    return Promise.reject(error);
  },
);

export interface PortalCustomer {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  status: string;
  plan_name: string | null;
}

export interface DashboardData {
  status: string;
  plan: { name: string; download_mbps: number; upload_mbps: number } | null;
  outstanding_balance: string;
  session: { ip_address: string; started_at: string; bytes_in: number; bytes_out: number } | null;
  recent_invoices: Array<{ id: string; amount: string; due_date: string; status: string }>;
}

export interface PortalInvoice {
  id: string;
  amount: string;
  due_date: string;
  status: string;
  issued_at: string;
  paid_at: string | null;
  plan_name: string | null;
  total_paid: string;
}

export const portalLogin = (email: string, password: string) =>
  portalClient.post('/auth/login', { email, password });

export const getPortalMe = () => portalClient.get<PortalCustomer>('/me');
export const getPortalDashboard = () => portalClient.get<DashboardData>('/dashboard');
export const getPortalInvoices = (params: { page?: number; size?: number }) =>
  portalClient.get<{ items: PortalInvoice[]; total: number; page: number; page_size: number }>('/invoices', { params });
export const downloadPortalInvoicePdf = (id: string) =>
  portalClient.get(`/invoices/${id}/pdf`, { responseType: 'blob' });
export const getPortalUsage = (days?: number) =>
  portalClient.get<Array<{ date: string; bytes_in: number; bytes_out: number; peak_download_mbps: string; peak_upload_mbps: string }>>('/usage', { params: { days: days || 30 } });
export const getPortalSessions = (params: { page?: number; size?: number }) =>
  portalClient.get<Array<{ id: string; ip_address: string; mac_address: string; started_at: string; ended_at: string | null; bytes_in: number; bytes_out: number }>>('/sessions', { params });
