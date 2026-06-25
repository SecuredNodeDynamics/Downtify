import { computed, ref } from 'vue'

import API from '/src/model/api'

const SEARCH_RESULT_FILTER_KEY = 'downtify-search-result-filter'

const searchTerm = ref('')
const results = ref()
const isSearching = ref(false)
const error = ref(false)
const errorValue = ref('')

function loadResultFilter() {
  try {
    const saved = globalThis.localStorage?.getItem(SEARCH_RESULT_FILTER_KEY)
    if (saved === 'albums' || saved === 'tracks' || saved === 'both') {
      return saved
    }
  } catch {
    // Ignore storage read failures in restricted environments.
  }
  return 'both'
}

const resultFilter = ref('both')
let resultFilterHydrated = false

function hydrateResultFilter() {
  if (resultFilterHydrated) return
  resultFilter.value = loadResultFilter()
  resultFilterHydrated = true
}

function setResultFilter(mode) {
  if (mode !== 'albums' && mode !== 'tracks' && mode !== 'both') return
  hydrateResultFilter()
  resultFilter.value = mode
  try {
    globalThis.localStorage?.setItem(SEARCH_RESULT_FILTER_KEY, mode)
  } catch {
    // Ignore storage write failures in restricted environments.
  }
}

function filterResults(items) {
  const list = Array.isArray(items) ? items : []
  if (resultFilter.value === 'albums') {
    return list.filter((item) => item?.media_type === 'album')
  }
  if (resultFilter.value === 'tracks') {
    return list.filter((item) => item?.media_type !== 'album')
  }
  return list
}

const filteredResults = computed(() => filterResults(results.value))

function useSearchManager() {
  hydrateResultFilter()
  function isValid(str) {
    return isValidSearch(str) || isValidURL(str)
  }
  function isValidSearch(str) {
    if (
      str === '' ||
      str.includes('://open.spotify.com/track/') ||
      str.includes('://open.spotify.com/album/') ||
      str.includes('://open.spotify.com/playlist/') ||
      str.includes('://open.spotify.com/show/') ||
      str.includes('://open.spotify.com/artist/')
    ) {
      return false
    }
    return true
  }
  function isValidURL(str) {
    return (
      str.includes('://open.spotify.com/track/') ||
      str.includes('://open.spotify.com/album/') ||
      str.includes('://open.spotify.com/playlist/')
    )
  }

  function searchFor(query) {
    console.log('Searching for:', query)
    results.value = []
    isSearching.value = true
    searchTerm.value = query
    error.value = false
    errorValue.value = ''
    API.search(query)
      .then((res) => {
        console.log('Received Search Data:', res.data)
        if (res.status === 200) {
          results.value = res.data
          isSearching.value = false
          void API.refreshLibraryInBackground()
        } else {
          console.error('Error Searching:', res)
          isSearching.value = false
          error.value = true
          errorValue.value = res.toString()
        }
      })
      .catch((err) => {
        console.error('Other Error Searching:', err.message)
        isSearching.value = false
        error.value = true
        errorValue.value = err.message
      })
  }

  return {
    searchTerm,
    isSearching,
    results,
    error,
    errorValue,
    resultFilter,
    setResultFilter,
    filterResults,
    filteredResults,
    searchFor,
    isValid,
    isValidSearch,
    isValidURL,
  }
}

export { useSearchManager }
