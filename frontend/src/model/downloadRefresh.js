import { ref } from 'vue'

const loading = ref(false)
// The Queue page only needs a header refresh on the tabs that fetch data
// (History/Manage); the live Queue tab updates over the WebSocket. The view
// toggles this so the header button hides when refreshing would do nothing.
const visible = ref(false)
let refreshHandler = null

// Keep the spinner visible long enough to register as feedback even when the
// underlying refresh resolves almost instantly (a warm cache or the embedded
// on-device backend can return before the browser paints a single frame).
const MIN_VISIBLE_MS = 500

export function useDownloadRefresh() {
  function register(handler) {
    refreshHandler = handler || null
  }

  function unregister() {
    refreshHandler = null
    visible.value = false
    loading.value = false
  }

  async function refresh() {
    if (!refreshHandler || loading.value) return
    loading.value = true
    const startedAt = Date.now()
    try {
      await refreshHandler()
    } finally {
      const remaining = MIN_VISIBLE_MS - (Date.now() - startedAt)
      if (remaining > 0) {
        await new Promise((resolve) => setTimeout(resolve, remaining))
      }
      loading.value = false
    }
  }

  function setLoading(value) {
    loading.value = Boolean(value)
  }

  function setVisible(value) {
    visible.value = Boolean(value)
  }

  return {
    loading,
    visible,
    register,
    unregister,
    refresh,
    setLoading,
    setVisible,
  }
}
