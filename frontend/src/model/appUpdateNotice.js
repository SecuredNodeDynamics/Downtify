import { onMounted, ref } from 'vue'

import { checkDowntifyVersion } from './appVersion'
import { openSettingsModal } from './settingsModal'

const updateAvailable = ref(false)
let checkPromise = null

async function refresh(refreshCache = false) {
  if (!refreshCache && checkPromise) {
    await checkPromise
    return
  }

  checkPromise = (async () => {
    try {
      const status = await checkDowntifyVersion({ refresh: refreshCache })
      updateAvailable.value = Boolean(status?.update_available)
    } catch {
      updateAvailable.value = false
    } finally {
      checkPromise = null
    }
  })()

  await checkPromise
}

export function useAppUpdateNotice() {
  onMounted(() => refresh())

  function openUpdateSettings() {
    openSettingsModal('help')
  }

  return { updateAvailable, refresh, openUpdateSettings }
}
