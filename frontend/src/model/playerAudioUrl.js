export function normalizeAudioUrl(url) {
  const value = String(url || '').trim()
  if (!value) return ''
  try {
    const resolved = value.includes('://')
      ? new URL(value)
      : new URL(
          value,
          typeof window !== 'undefined' && window.location?.origin
            ? window.location.origin
            : 'http://local.invalid'
        )
    return `${resolved.pathname}${resolved.search}`
  } catch {
    return value
  }
}

export function isSameAudioUrl(currentUrl, nextUrl) {
  if (!currentUrl || !nextUrl) return false
  return normalizeAudioUrl(currentUrl) === normalizeAudioUrl(nextUrl)
}
