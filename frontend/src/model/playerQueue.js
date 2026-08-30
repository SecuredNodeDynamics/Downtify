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
