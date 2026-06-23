export function albumKey(artist, album) {
  return `${artist}\u0000${album}`
}

export function groupArtists(items) {
  const grouped = new Map()

  for (const item of items) {
    const name = item.artist || 'Unknown Artist'
    if (!grouped.has(name)) {
      grouped.set(name, {
        name,
        files: [],
        albums: new Set(),
      })
    }
    const artist = grouped.get(name)
    artist.files.push(item.file)
    if (item.album) artist.albums.add(item.album)
  }

  return Array.from(grouped.values())
    .map((artist) => ({
      name: artist.name,
      files: artist.files,
      albumCount: artist.albums.size,
      previewFiles: artist.files.slice(0, 3),
    }))
    .sort((a, b) => a.name.localeCompare(b.name))
}

export function groupAlbums(items) {
  const grouped = new Map()

  for (const item of items) {
    if (!item.album) continue
    const key = albumKey(item.artist, item.album)
    if (!grouped.has(key)) {
      grouped.set(key, {
        key,
        name: item.album,
        artist: item.artist,
        files: [],
      })
    }
    grouped.get(key).files.push(item.file)
  }

  return Array.from(grouped.values())
    .map((album) => ({
      ...album,
      coverFile: album.files[0],
    }))
    .sort(
      (a, b) =>
        a.artist.localeCompare(b.artist) || a.name.localeCompare(b.name)
    )
}

export function groupGenres(items, unknownLabel = 'Unknown') {
  const grouped = new Map()

  for (const item of items) {
    const name = String(item.genre || '').trim() || unknownLabel
    if (!grouped.has(name)) {
      grouped.set(name, {
        name,
        files: [],
      })
    }
    grouped.get(name).files.push(item.file)
  }

  return Array.from(grouped.values()).sort((a, b) => {
    if (a.name === unknownLabel) return 1
    if (b.name === unknownLabel) return -1
    return a.name.localeCompare(b.name)
  })
}

export function itemMap(items) {
  return new Map(items.map((item) => [item.file, item]))
}

export function matchesLibraryFilter(item, query) {
  const q = String(query || '')
    .trim()
    .toLowerCase()
  if (!q) return true
  return [item.title, item.artist, item.album, item.genre, item.file].some(
    (part) =>
      String(part || '')
        .toLowerCase()
        .includes(q)
  )
}
