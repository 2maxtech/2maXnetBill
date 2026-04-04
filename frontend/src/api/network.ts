import client from './client';

export interface PppoeSession {
  '.id': string;
  name: string;
  service: string;
  'caller-id': string;
  address: string;
  uptime: string;
  encoding: string;
}

export interface NetworkStatus {
  connected: boolean;
  identity?: string;
  uptime?: string;
  cpu_load?: string;
  free_memory?: string;
  error?: string;
}

export const getActiveSessions = () =>
  client.get<{ sessions: PppoeSession[]; total: number }>('/network/active-sessions');

export const getNetworkStatus = () =>
  client.get<NetworkStatus>('/network/status');

export const getSubscribers = () =>
  client.get<{ subscribers: any[]; total: number }>('/network/subscribers');
