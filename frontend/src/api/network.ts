import client from './client';

// Firewall
export const getFirewallRuleset = () => client.get('/network/firewall/ruleset');
export const getFirewallTables = () => client.get('/network/firewall/tables');
export const addFirewallRule = (data: { table: string; chain: string; rule: string; family?: string }) =>
  client.post('/network/firewall/rule', data);
export const deleteFirewallRule = (data: { table: string; chain: string; handle: number; family?: string }) =>
  client.delete('/network/firewall/rule', { data });
export const flushFirewallChain = (data: { table: string; chain: string; family?: string }) =>
  client.post('/network/firewall/flush', data);

// Network
export const getInterfaces = () => client.get('/network/interfaces');
export const getRoutes = () => client.get('/network/routes');
export const addRoute = (data: { destination: string; gateway: string; interface?: string }) =>
  client.post('/network/route', data);
export const deleteRoute = (data: { destination: string }) =>
  client.delete('/network/route', { data });
export const getNatRules = () => client.get('/network/nat');
export const addNatMasquerade = (data: { out_interface: string }) =>
  client.post('/network/nat/masquerade', data);
export const addPortForward = (data: { protocol: string; dport: number; dest_ip: string; dest_port: number; in_interface?: string }) =>
  client.post('/network/nat/port-forward', data);

// DHCP
export const getDhcpLeases = () => client.get('/network/dhcp/leases');
export const getDhcpConfig = () => client.get<{ config: string }>('/network/dhcp/config');
export const applyDhcpConfig = (config: string) => client.post('/network/dhcp/config', { config });

// DNS
export const getDnsConfig = () => client.get<{ config: string }>('/network/dns/config');
export const addDnsEntry = (data: { domain: string; ip: string }) => client.post('/network/dns/entry', data);
export const getUpstreamDns = () => client.get('/network/dns/upstream');
