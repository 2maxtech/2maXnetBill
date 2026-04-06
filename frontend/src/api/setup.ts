import api from './client'
import axios from 'axios'

export interface SetupStatus {
  configured: boolean
  deployment_mode: string
}

export interface SetupRequest {
  company_name: string
  admin_username: string
  admin_email: string
  admin_password: string
  router_name?: string
  router_url?: string
  router_username?: string
  router_password?: string
}

export interface SetupResponse {
  access_token: string
  refresh_token: string
  user_id: string
  router_created: boolean
  message: string
}

export interface UpdateInfo {
  update_available: boolean
  version?: string
  release_notes?: string
  release_date?: string
  download_url?: string
}

export function getSetupStatus() {
  return axios.get<SetupStatus>('/api/v1/setup/status')
}

export function initializeSetup(data: SetupRequest) {
  return axios.post<SetupResponse>('/api/v1/setup/initialize', data)
}

export function checkForUpdate() {
  return api.get<UpdateInfo>('/system/update-check')
}
