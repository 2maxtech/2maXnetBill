import client from './client';

export interface RouterType {
  id: string;
  name: string;
  url: string;
  username: string;
  location: string | null;
  is_active: boolean;
  maintenance_mode: boolean;
  maintenance_message: string | null;
  created_at: string;
}

export interface RouterStatus {
  id: string;
  name: string;
  connected: boolean;
  identity?: string;
  uptime?: string;
  cpu_load?: string;
  free_memory?: number;
  total_memory?: number;
  active_sessions?: number;
  version?: string;
  error?: string;
}

export interface AreaType {
  id: string;
  name: string;
  description: string | null;
  router_id: string | null;
  router: RouterType | null;
  created_at: string;
}

export const getRouters = () => client.get<RouterType[]>('/routers/');
export const createRouter = (data: any) => client.post<RouterType>('/routers/', data);
export const updateRouter = (id: string, data: any) => client.put<RouterType>(`/routers/${id}`, data);
export const deleteRouter = (id: string) => client.delete(`/routers/${id}`);
export const getRouterStatus = (id: string) => client.get<RouterStatus>(`/routers/${id}/status`);
export const importFromRouter = (id: string) => client.post(`/routers/${id}/import`);
export const scanNetwork = (data: any) => client.post('/network/scan', data);

export const getAreas = () => client.get<AreaType[]>('/areas/');
export const createArea = (data: any) => client.post<AreaType>('/areas/', data);
export const updateArea = (id: string, data: any) => client.put<AreaType>(`/areas/${id}`, data);
export const deleteArea = (id: string) => client.delete(`/areas/${id}`);
