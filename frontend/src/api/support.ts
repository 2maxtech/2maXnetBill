import api from './client'

export interface SupportTicket {
  id: string
  subject: string
  description: string
  status: 'open' | 'in_progress' | 'resolved' | 'closed'
  category: string
  tenant_name: string | null
  tenant_email: string | null
  chat_history: string | null
  image_urls: string | null
  admin_notes: string | null
  owner_id: string | null
  created_at: string
}

export interface PaginatedTickets {
  items: SupportTicket[]
  total: number
  page: number
  page_size: number
}

export function getSupportTickets(params?: {
  status?: string
  category?: string
  search?: string
  page?: number
  page_size?: number
}) {
  return api.get<PaginatedTickets>('/support/tickets', { params })
}

export function getSupportTicket(id: string) {
  return api.get<SupportTicket>(`/support/tickets/${id}`)
}

export function updateSupportTicket(id: string, data: { status?: string; admin_notes?: string }) {
  return api.put<SupportTicket>(`/support/tickets/${id}`, data)
}
