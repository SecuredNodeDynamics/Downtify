import { ref } from 'vue'

const libraryFilter = ref('')
let focusHandler = null

export function useMobileSearch() {
  function registerFocusHandler(handler) {
    focusHandler = handler || null
  }

  function openSheet() {
    const sheet = document.getElementById('mobile-search-sheet')
    if (!sheet) return
    sheet.checked = true
  }

  function focusSearchInput() {
    if (focusHandler) {
      focusHandler()
      return
    }
    const input = document.getElementById('mobile-search-input')
    input?.focus({ preventScroll: true })
  }

  function openSheetAndFocus() {
    openSheet()
    // Must run in the same user-gesture turn for mobile keyboards (iOS/Android).
    focusSearchInput()
    requestAnimationFrame(() => {
      focusSearchInput()
      requestAnimationFrame(focusSearchInput)
    })
    window.setTimeout(focusSearchInput, 50)
    window.setTimeout(focusSearchInput, 150)
  }

  function closeSheet() {
    const sheet = document.getElementById('mobile-search-sheet')
    if (sheet) sheet.checked = false
  }

  function setLibraryFilter(query) {
    libraryFilter.value = String(query || '').trim()
  }

  function clearLibraryFilter() {
    libraryFilter.value = ''
  }

  return {
    libraryFilter,
    registerFocusHandler,
    openSheet,
    openSheetAndFocus,
    focusSearchInput,
    closeSheet,
    setLibraryFilter,
    clearLibraryFilter,
  }
}
