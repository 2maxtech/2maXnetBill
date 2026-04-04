import client from './client';

export interface TicketMessage {
  id: string;
  ticket_id: string;
  sender_type: string;
  sender_id: string;
  message: string;
  created_at: string;
}

export interface TicketType {
  id: string;
  customer_id: string;
  subject: string;
  status: string;
  priority: string;
  assigned_to: string | null;
  resolved_at: string | null;
  created_at: string;
  messages: TicketMessage[];
}

export const getTickets = (params?: any) =>
  client.get<TicketType[]>('/tickets/', { params });
export const createTicket = (data: any) => client.post<TicketType>('/tickets/', data);
export const getTicket = (id: string) => client.get<TicketType>(`/tickets/${id}`);
export const updateTicket = (id: string, data: any) =>
  client.put<TicketType>(`/tickets/${id}`, data);
export const addTicketMessage = (id: string, data: any) =>
  client.post(`/tickets/${id}/messages`, data);
