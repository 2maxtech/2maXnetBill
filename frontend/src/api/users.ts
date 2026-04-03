import client from './client';

export interface StaffUser {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'billing' | 'technician';
  is_active: boolean;
  created_at: string;
}

export const getUsers = () => client.get<StaffUser[]>('/system/users/');
export const createUser = (data: Record<string, unknown>) => client.post('/system/users/', data);
export const updateUser = (id: string, data: Record<string, unknown>) => client.put(`/system/users/${id}`, data);
export const deleteUser = (id: string) => client.delete(`/system/users/${id}`);
