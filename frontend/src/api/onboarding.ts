import api from './client'

export interface OnboardingStatus {
  has_router: boolean
  has_plan: boolean
  has_customer: boolean
  has_billing_config: boolean
  has_notifications: boolean
  dismissed: boolean
  completed: number
  total: number
}

export function getOnboardingStatus() {
  return api.get<OnboardingStatus>('/onboarding/status')
}

export function dismissOnboarding() {
  return api.post('/onboarding/dismiss')
}
