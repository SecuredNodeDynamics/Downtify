export function pathParts(file) {
  return String(file || '')
    .split('/')
    .map((part) => part.trim())
    .filter(Boolean)
}

export function displayNameFromFile(file) {
  const value = String(file || '')
  const slash = value.lastIndexOf('/')
  return slash >= 0 ? value.slice(slash + 1) : value
}

export function artistFromPath(file, unknownArtist = 'Unknown Artist') {
  const parts = pathParts(file)
  if (parts.length > 1) return parts[0]

  const name = displayNameFromFile(file).replace(/\.[^/.]+$/, '')
  const separator = name.indexOf(' - ')
  if (separator > 0) return name.slice(0, separator).trim()

  return unknownArtist
}

export function albumFromPath(file) {
  const parts = pathParts(file)
  if (parts.length > 2) return parts[1]
  return ''
}

export function normalizeLibraryItem(item, options = {}) {
  const unknownArtist = options.unknownArtist || 'Unknown Artist'
  const file = String(item?.file || '')
  const artist =
    String(item?.artist || '').trim() || artistFromPath(file, unknownArtist)
  const album = String(item?.album || '').trim() || albumFromPath(file)
  const title =
    String(item?.title || '').trim() ||
    displayNameFromFile(file).replace(/\.[^/.]+$/, '')
  const genre = String(item?.genre || '').trim()
  const browseGenre = String(item?.browse_genre || '').trim() || genre
  return {
    ...item,
    file,
    title,
    artist,
    album,
    genre,
    browse_genre: browseGenre,
  }
}

export function albumKey(artist, album) {
  return `${artist}\u0000${album}`
}

export function libraryCoverFolders(file) {
  const parts = pathParts(file)
  const folders = []
  if (parts.length > 2) {
    folders.push(`${parts[0]}/${parts[1]}`)
    folders.push(parts[0])
  } else if (parts.length > 1) {
    folders.push(parts[0])
  }
  return folders
}

export function groupArtists(items, options = {}) {
  const grouped = new Map()

  for (const raw of items) {
    const item = normalizeLibraryItem(raw, options)
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
      albumNames: Array.from(artist.albums).sort((a, b) => a.localeCompare(b)),
      previewFiles: artist.files.slice(0, 3),
    }))
    .sort((a, b) => a.name.localeCompare(b.name))
}

export function groupAlbums(items, options = {}) {
  const grouped = new Map()

  for (const raw of items) {
    const item = normalizeLibraryItem(raw, options)
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
      (a, b) => a.artist.localeCompare(b.artist) || a.name.localeCompare(b.name)
    )
}

export function genreCoverFiles(files) {
  const seen = new Set()
  const covers = []

  for (const file of files || []) {
    const parts = pathParts(file)
    const key =
      parts.length > 2
        ? `${parts[0]}\u0000${parts[1]}`
        : parts.length > 1
        ? parts[0]
        : String(file || '')
    if (!key || seen.has(key)) continue
    seen.add(key)
    covers.push(file)
    if (covers.length >= 4) break
  }

  return covers
}

export function groupGenres(items, unknownLabel = 'Unknown', options = {}) {
  const grouped = new Map()

  for (const raw of items) {
    const item = normalizeLibraryItem(raw, options)
    const name =
      String(item.browse_genre || item.genre || '').trim() || unknownLabel
    if (!grouped.has(name)) {
      grouped.set(name, {
        name,
        files: [],
        subgenres: new Set(),
      })
    }
    const bucket = grouped.get(name)
    bucket.files.push(item.file)
    if (item.genre && item.genre !== name) {
      bucket.subgenres.add(item.genre)
    }
  }

  return Array.from(grouped.values())
    .map((genre) => ({
      name: genre.name,
      files: genre.files,
      coverFiles: genreCoverFiles(genre.files),
      subgenres: Array.from(genre.subgenres).sort((a, b) => a.localeCompare(b)),
    }))
    .sort((a, b) => {
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
  return [
    item.title,
    item.artist,
    item.album,
    item.genre,
    item.browse_genre,
    item.file,
  ].some((part) =>
    String(part || '')
      .toLowerCase()
      .includes(q)
  )
}
