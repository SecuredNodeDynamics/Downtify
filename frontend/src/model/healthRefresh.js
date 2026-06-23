import { ref } from 'vue'

const loading = ref(false)
let refreshHandler = null

export function useHealthRefresh() {
  function register(handler) {
    refreshHandler = handler || null
  }

  function unregister() {
    refreshHandler = null
  }

  async function refresh() {
    if (!refreshHandler) return
    await refreshHandler()
  }

  function setLoading(value) {
    loading.value = Boolean(value)
  }

  return {
    loading,
    register,
    unregister,
    refresh,
    setLoading,
  }
}
