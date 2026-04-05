import { ref, computed } from 'vue'
import { setTenantId } from '../api/client'

interface ImpersonatedOrg {
  id: string
  username: string
  company_name: string
}

const impersonating = ref<ImpersonatedOrg | null>(null)

export function useImpersonate() {
  const isImpersonating = computed(() => !!impersonating.value)

  function enterOrg(org: ImpersonatedOrg) {
    impersonating.value = org
    setTenantId(org.id)
  }

  function exitOrg() {
    impersonating.value = null
    setTenantId(null)
  }

  return { impersonating, isImpersonating, enterOrg, exitOrg }
}
