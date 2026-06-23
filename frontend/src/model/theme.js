import { ref } from 'vue'

export const THEME_STORAGE_KEY = 'downtify-theme'

const currentTheme = ref('')

const lightAlias = ref('light')
const darkAlias = ref('dark')

let initialized = false

function readStoredTheme() {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY)
    if (stored === 'light' || stored === 'dark') {
      return stored
    }
  } catch {
    // Ignore storage errors (private mode, blocked storage, etc.).
  }
  return null
}

function persistTheme(theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    // Ignore storage errors.
  }
}

export function useBinaryThemeManager({
  useSystem = true,
  initialTheme = '',
  newLightAlias = '',
  newDarkAlias = '',
} = {}) {
  function setLightAlias(alias) {
    lightAlias.value = alias
    _updateDocument()
  }
  function setDarkAlias(alias) {
    darkAlias.value = alias
    _updateDocument()
  }

  function getSystemTheme() {
    const darkThemeMq = window.matchMedia('(prefers-color-scheme: dark)')
    if (darkThemeMq.matches) {
      return 'dark'
    }
    return 'light'
  }

  function setTheme(newTheme) {
    if (newTheme !== 'light' && newTheme !== 'dark') {
      return
    }
    currentTheme.value = newTheme
    persistTheme(newTheme)
    _updateDocument()
  }

  function switchTheme() {
    setTheme(currentTheme.value === 'dark' ? 'light' : 'dark')
  }

  function _updateDocument() {
    document.documentElement.setAttribute(
      'data-theme',
      currentTheme.value === 'dark' ? darkAlias.value : lightAlias.value
    )
  }

  if (!initialized) {
    initialized = true
    const storedTheme = readStoredTheme()
    if (storedTheme) {
      currentTheme.value = storedTheme
    } else if (initialTheme === 'light' || initialTheme === 'dark') {
      currentTheme.value = initialTheme
    } else if (useSystem) {
      currentTheme.value = getSystemTheme()
    } else {
      currentTheme.value = 'dark'
    }
  }

  if (newLightAlias) setLightAlias(newLightAlias)
  if (newDarkAlias) setDarkAlias(newDarkAlias)

  _updateDocument()

  return {
    currentTheme,
    setLightAlias,
    setDarkAlias,
    getSystemTheme,
    setTheme,
    switchTheme,
  }
}
