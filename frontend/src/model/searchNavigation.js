export function resolveSearchRouteQuery(route) {
  const queryParam = route?.query?.q
  if (queryParam != null && String(queryParam).trim()) {
    return String(queryParam).trim()
  }
  const legacyParam = route?.params?.query
  if (legacyParam != null && String(legacyParam).trim()) {
    try {
      return decodeURIComponent(String(legacyParam).trim())
    } catch {
      return String(legacyParam).trim()
    }
  }
  return ''
}

export function buildSearchRoute(query) {
  const trimmed = String(query || '').trim()
  if (!trimmed) {
    return { name: 'Search' }
  }
  return { name: 'Search', query: { q: trimmed } }
}
