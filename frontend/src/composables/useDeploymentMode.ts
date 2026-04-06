export const isOnPremise = import.meta.env.VITE_DEPLOYMENT_MODE === 'onpremise'
export const isSaaS = !isOnPremise
