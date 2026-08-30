export function parseFilenameTrack(file) {
  const noExt = String(file || '').replace(/\.[^.]+$/, '')
  let artist = ''
  let title = noExt
  const dash = noExt.indexOf(' - ')
  if (dash > 0) {
    artist = noExt.slice(0, dash).trim()
    title = noExt.slice(dash + 3).trim()
  }
  return { title, artist }
}

export function enrichTrackFromLibrary(file, meta) {
  const parsed = parseFilenameTrack(file)
  return {
    title: String(meta?.title || '').trim() || parsed.title,
    artist: String(meta?.artist || '').trim() || parsed.artist,
    album: String(meta?.album || '').trim(),
  }
}

export function albumsByArtist(albums, artistName) {
  const key = String(artistName || '')
    .trim()
    .toLowerCase()
  if (!key) return []
  return (albums || []).filter(
    (album) => String(album?.artist || '').trim().toLowerCase() === key
  )
}

export function nextAlbumAfter(albums, artistName, currentAlbumName) {
  const same = albumsByArtist(albums, artistName)
  if (!same.length) return null
  const currentKey = String(currentAlbumName || '')
    .trim()
    .toLowerCase()
  const index = same.findIndex(
    (album) => String(album?.name || '').trim().toLowerCase() === currentKey
  )
  if (index < 0) return same[0]
  return same[index + 1] || null
}

export function filesWithFollowOnAlbum(files, nextAlbum) {
  const current = Array.isArray(files) ? files.filter(Boolean) : []
  const extra = (nextAlbum?.files || []).filter(
    (file) => file && !current.includes(file)
  )
  return { files: [...current, ...extra], followOnStart: extra.length ? current.length : -1 }
}

export function nextIndexInOrder({
  length,
  currentIndex,
  shuffle = false,
  shuffleOrder = [],
  shufflePos = 0,
  repeatMode = 'off',
} = {}) {
  const size = Number(length) || 0
  if (size <= 0) return -1
  if (shuffle) {
    if (!Array.isArray(shuffleOrder) || shuffleOrder.length !== size) return -1
    const nextPos = Number(shufflePos) + 1
    if (nextPos >= shuffleOrder.length) {
      return repeatMode === 'all' ? shuffleOrder[0] : -1
    }
    return shuffleOrder[nextPos]
  }
  const i = Number(currentIndex) + 1
  if (i >= size) return repeatMode === 'all' ? 0 : -1
  return i
}

export function prevIndexInOrder({
  length,
  currentIndex,
  shuffle = false,
  shuffleOrder = [],
  shufflePos = 0,
  repeatMode = 'off',
} = {}) {
  const size = Number(length) || 0
  if (size <= 0) return -1
  if (shuffle) {
    if (!Array.isArray(shuffleOrder) || shuffleOrder.length !== size) return -1
    const prevPos = Number(shufflePos) - 1
    if (prevPos < 0) {
      return repeatMode === 'all' ? shuffleOrder[size - 1] : -1
    }
    return shuffleOrder[prevPos]
  }
  const i = Number(currentIndex) - 1
  if (i < 0) return repeatMode === 'all' ? size - 1 : 0
  return i
}
