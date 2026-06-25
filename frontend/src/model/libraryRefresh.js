import { ref } from 'vue'

const loading = ref(false)
const failed = ref(false)
let refreshHandler = null

export function useLibraryRefresh() {
  function register(handler) {
    refreshHandler = handler || null
  }

  function unregister() {
    refreshHandler = null
  }

  async function refresh() {
    if (!refreshHandler) return
    failed.value = false
    await refreshHandler()
  }

  function setLoading(value) {
    loading.value = Boolean(value)
  }

  function setFailed(value) {
    failed.value = Boolean(value)
  }

  return {
    loading,
    failed,
    register,
    unregister,
    refresh,
    setLoading,
    setFailed,
  }
}
