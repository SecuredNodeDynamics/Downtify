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
    (album) =>
      String(album?.artist || '')
        .trim()
        .toLowerCase() === key
  )
}

export function nextAlbumAfter(albums, artistName, currentAlbumName) {
  const same = albumsByArtist(albums, artistName)
  if (!same.length) return null
  const currentKey = String(currentAlbumName || '')
    .trim()
    .toLowerCase()
  const index = same.findIndex(
    (album) =>
      String(album?.name || '')
        .trim()
        .toLowerCase() === currentKey
  )
  if (index < 0) return same[0]
  return same[index + 1] || null
}

export function filesWithFollowOnAlbum(files, nextAlbum) {
  const current = Array.isArray(files) ? files.filter(Boolean) : []
  const extra = (nextAlbum?.files || []).filter(
    (file) => file && !current.includes(file)
  )
  return {
    files: [...current, ...extra],
    followOnStart: extra.length ? current.length : -1,
  }
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

export function pickRandomStartIndex(
  length,
  avoidIndexes = [],
  random = Math.random
) {
  const size = Math.max(0, Number(length) || 0)
  if (size <= 1) return 0
  const avoid = new Set()
  for (const index of avoidIndexes) {
    if (Number.isInteger(index) && index >= 0 && index < size) {
      avoid.add(index)
    }
  }
  const pool = []
  for (let i = 0; i < size; i++) {
    if (!avoid.has(i)) pool.push(i)
  }
  const choices = pool.length ? pool : [...Array(size).keys()]
  const roll = Number(random())
  const offset = Number.isFinite(roll)
    ? Math.min(
        choices.length - 1,
        Math.max(0, Math.floor(roll * choices.length))
      )
    : 0
  return choices[offset]
}

let lastGenreStartFile = ''

export function resetGenrePlayStartMemory() {
  lastGenreStartFile = ''
}

export function nextGenrePlaylistStart(
  files,
  extraAvoidFiles = [],
  random = Math.random
) {
  const list = Array.isArray(files) ? files : []
  if (!list.length) return 0
  const avoidIndexes = []
  for (const file of [lastGenreStartFile, ...extraAvoidFiles]) {
    if (!file) continue
    const index = list.indexOf(file)
    if (index >= 0) avoidIndexes.push(index)
  }
  const startIndex = pickRandomStartIndex(list.length, avoidIndexes, random)
  lastGenreStartFile = list[startIndex] || ''
  return startIndex
}
