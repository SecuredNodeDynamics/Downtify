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

export function splitArtistNames(value) {
  const names = []
  const seen = new Set()
  for (const part of String(value || '').split(/[,/&]+/)) {
    const trimmed = part.trim()
    if (!trimmed) continue
    const key = trimmed.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    names.push(trimmed)
  }
  return names
}

export function libraryItemArtists(item, options = {}) {
  const unknownArtist = options.unknownArtist || 'Unknown Artist'
  const file = String(item?.file || '')
  const primary =
    String(item?.artist || '').trim() || artistFromPath(file, unknownArtist)
  const artists = []
  const seen = new Set()
  const add = (name) => {
    const trimmed = String(name || '').trim()
    if (!trimmed) return
    const key = trimmed.toLowerCase()
    if (seen.has(key)) return
    seen.add(key)
    artists.push(trimmed)
  }

  // Add a combined artist string only when it represents a single artist.
  // Splitting first means a collaboration ("A, B") becomes one entry per
  // individual artist instead of a combined card, while single artists whose
  // names legitimately contain separators are preserved verbatim.
  const addNames = (value) => {
    const names = splitArtistNames(value)
    if (names.length > 1) {
      for (const name of names) add(name)
    } else {
      add(value)
    }
  }

  // A multi-entry list is already split into individual credited artists, so
  // trust it verbatim. A single entry, however, can still be a combined
  // collaboration string ("Ariana Grande, Nicki Minaj") produced by a source
  // that didn't separate the artists — split it so each performer gets their
  // own card instead of one merged card.
  if (Array.isArray(item?.artists) && item.artists.length > 1) {
    for (const artist of item.artists) add(artist)
  } else if (Array.isArray(item?.artists) && item.artists.length === 1) {
    addNames(item.artists[0])
  } else {
    addNames(primary)
  }

  // Fall back to the folder name only when nothing else identified an artist,
  // splitting a combined collaboration folder into individual artists too.
  if (!artists.length) {
    const parts = pathParts(file)
    if (parts.length > 1) addNames(parts[0])
  }

  if (!artists.length) add(unknownArtist)
  return artists
}

export function libraryArtistsLabel(item, options = {}) {
  const artists = libraryItemArtists(item, options)
  return artists.join(', ')
}

export function normalizeLibraryItem(item, options = {}) {
  const unknownArtist = options.unknownArtist || 'Unknown Artist'
  const file = String(item?.file || '')
  const artist =
    String(item?.artist || '').trim() || artistFromPath(file, unknownArtist)
  const artists = libraryItemArtists({ ...item, artist, file }, options)
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
    artists,
    album,
    genre,
    browse_genre: browseGenre,
  }
}

export function albumArtistsLabel(album) {
  if (Array.isArray(album?.artists) && album.artists.length > 1) {
    return album.artists.join(', ')
  }
  return String(album?.artist || album?.primaryArtist || '').trim()
}

export function albumKey(artist, album) {
  return `${artist}\u0000${album}`
}

export function artistBrowseKey(name) {
  return String(name || '')
    .normalize('NFKC')
    .trim()
    .replace(/\s+/g, ' ')
    .toLowerCase()
}

function artistLooseKey(name) {
  return artistBrowseKey(name)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\p{L}\p{N}\s]/gu, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function editDistanceWithinOne(left, right) {
  const a = String(left || '')
  const b = String(right || '')
  if (a === b) return 0
  if (Math.abs(a.length - b.length) > 1) return 2

  let edits = 0
  let i = 0
  let j = 0
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      i += 1
      j += 1
      continue
    }
    edits += 1
    if (edits > 1) return 2
    if (a.length > b.length) {
      i += 1
    } else if (b.length > a.length) {
      j += 1
    } else {
      i += 1
      j += 1
    }
  }
  return edits + (i < a.length || j < b.length ? 1 : 0)
}

function artistNamesLookEquivalent(left, right) {
  const a = artistLooseKey(left)
  const b = artistLooseKey(right)
  if (!a || !b) return false
  if (a === b) return true

  const leftWords = a.split(' ')
  const rightWords = b.split(' ')
  if (leftWords.length !== rightWords.length) return false
  if (leftWords.length > 4) return false

  let totalEdits = 0
  for (let index = 0; index < leftWords.length; index += 1) {
    const leftWord = leftWords[index]
    const rightWord = rightWords[index]
    if (leftWord === rightWord) continue
    if (Math.min(leftWord.length, rightWord.length) < 4) return false
    const edits = editDistanceWithinOne(leftWord, rightWord)
    if (edits > 1) return false
    totalEdits += edits
    if (totalEdits > 2) return false
  }
  return totalEdits > 0
}

function cleanArtistDisplayName(name) {
  return String(name || '')
    .normalize('NFKC')
    .trim()
    .replace(/\s+/g, ' ')
}

function artistDisplayScore(name) {
  const value = cleanArtistDisplayName(name)
  if (!value) return 0
  return value.split(/\s+/).reduce((score, word) => {
    const startsWell = /^[\p{Lu}\d]/u.test(word) ? 1 : 0
    const acronymBonus = word.length > 1 && word === word.toUpperCase() ? 0.25 : 0
    const diacriticBonus = /[^\u0000-\u007f]/.test(word) ? 0.5 : 0
    return score + startsWell + acronymBonus + diacriticBonus
  }, 0)
}

function chooseArtistDisplayName(current, candidate) {
  const currentName = cleanArtistDisplayName(current)
  const candidateName = cleanArtistDisplayName(candidate)
  if (!currentName) return candidateName
  if (!candidateName) return currentName
  if (
    artistBrowseKey(currentName) !== artistBrowseKey(candidateName) &&
    !artistNamesLookEquivalent(currentName, candidateName)
  ) {
    return currentName
  }
  const currentScore = artistDisplayScore(currentName)
  const candidateScore = artistDisplayScore(candidateName)
  if (candidateScore !== currentScore) {
    return candidateScore > currentScore ? candidateName : currentName
  }
  return candidateName.length > currentName.length ? candidateName : currentName
}

function artistGroupKeyForName(grouped, name) {
  const key = artistBrowseKey(name)
  if (!key || grouped.has(key)) return key

  for (const [existingKey, artist] of grouped.entries()) {
    if (artistNamesLookEquivalent(artist.name, name)) {
      return existingKey
    }
  }
  return key
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
    for (const name of libraryItemArtists(item, options)) {
      const key = artistGroupKeyForName(grouped, name)
      if (!key) continue

      if (!grouped.has(key)) {
        grouped.set(key, {
          name,
          files: [],
          albums: new Set(),
          fileSet: new Set(),
        })
      }

      const artist = grouped.get(key)
      artist.name = chooseArtistDisplayName(artist.name, name)
      if (!artist.fileSet.has(item.file)) {
        artist.fileSet.add(item.file)
        artist.files.push(item.file)
      }
      if (item.album) artist.albums.add(item.album)
    }
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
    const creditedArtists = libraryItemArtists(item, options)
    for (const browseArtist of creditedArtists) {
      const key = albumKey(browseArtist, item.album)
      if (!grouped.has(key)) {
        grouped.set(key, {
          key,
          name: item.album,
          artist: browseArtist,
          artists: creditedArtists,
          primaryArtist: item.artist,
          files: [],
          fileSet: new Set(),
        })
      }
      const album = grouped.get(key)
      if (!album.fileSet.has(item.file)) {
        album.fileSet.add(item.file)
        album.files.push(item.file)
      }
    }
  }

  return Array.from(grouped.values())
    .map((album) => ({
      key: album.key,
      name: album.name,
      artist: album.artist,
      artists: album.artists,
      primaryArtist: album.primaryArtist,
      files: album.files,
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

function artistsListEqual(left, right) {
  const a = Array.isArray(left) ? left : []
  const b = Array.isArray(right) ? right : []
  if (a.length !== b.length) return false
  return a.every((value, index) => value === b[index])
}

function titleCaseGenreLabel(value) {
  return String(value || '')
    .trim()
    .split(/\s+/)
    .map((word) => {
      if (word.includes('&')) return word.toUpperCase()
      return word
        .split('-')
        .map((part) =>
          part
            ? `${part.charAt(0).toUpperCase()}${part.slice(1).toLowerCase()}`
            : part
        )
        .join('-')
    })
    .join(' ')
}

export function libraryItemsEqual(current, next) {
  if (!Array.isArray(current) || !Array.isArray(next)) return false
  if (current.length !== next.length) return false
  for (let index = 0; index < current.length; index += 1) {
    const left = current[index]
    const right = next[index]
    if (!left || !right || left.file !== right.file) return false
    if (
      left.title !== right.title ||
      left.artist !== right.artist ||
      left.album !== right.album ||
      left.genre !== right.genre ||
      left.browse_genre !== right.browse_genre
    ) {
      return false
    }
    if (!artistsListEqual(left.artists, right.artists)) return false
  }
  return true
}

export function normalizeGenreDisplayName(name) {
  const raw = String(name || '').trim()
  if (!raw) return ''
  const folded = raw
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/-/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  if (folded === 'r b' || folded === 'rnb') return 'R&B'
  if (folded === 'hip hop' || folded === 'hiphop') return 'Hip-Hop'
  if (folded === 'edm' || folded === 'idm') return folded.toUpperCase()
  return titleCaseGenreLabel(raw)
}

export function libraryGenreName(item, unknownLabel = 'Unknown', options = {}) {
  const normalized = normalizeLibraryItem(item, options)
  const raw = String(normalized.browse_genre || normalized.genre || '').trim()
  if (!raw) return unknownLabel
  return normalizeGenreDisplayName(raw)
}

export function groupGenres(items, unknownLabel = 'Unknown', options = {}) {
  const grouped = new Map()

  for (const raw of items) {
    const item = normalizeLibraryItem(raw, options)
    const name = libraryGenreName(item, unknownLabel, options)
    if (!grouped.has(name)) {
      grouped.set(name, {
        name,
        files: [],
        subgenres: new Set(),
      })
    }
    const bucket = grouped.get(name)
    bucket.files.push(item.file)
    if (
      item.browse_genre &&
      normalizeGenreDisplayName(item.browse_genre) !== name
    ) {
      bucket.subgenres.add(normalizeGenreDisplayName(item.browse_genre))
    } else if (item.genre && normalizeGenreDisplayName(item.genre) !== name) {
      bucket.subgenres.add(normalizeGenreDisplayName(item.genre))
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

export function normalizeLibrarySearchQuery(query) {
  return String(query || '')
    .trim()
    .toLowerCase()
}

export function matchesLibraryField(field, query) {
  const q = normalizeLibrarySearchQuery(query)
  if (!q) return true
  return String(field || '')
    .toLowerCase()
    .includes(q)
}

export function matchesLibraryArtistName(artistName, query) {
  return matchesLibraryField(artistName, query)
}

export function matchesLibraryAlbumEntry(album, query) {
  const q = normalizeLibrarySearchQuery(query)
  if (!q) return true
  const artistFields = Array.isArray(album?.artists)
    ? album.artists
    : [album?.artist]
  return (
    matchesLibraryField(album.name, q) ||
    artistFields.some((artist) => matchesLibraryField(artist, q))
  )
}

export function matchesLibraryTrackItem(item, query) {
  const q = normalizeLibrarySearchQuery(query)
  if (!q) return true
  const artistFields = libraryItemArtists(item)
  return (
    matchesLibraryField(item.title, q) ||
    artistFields.some((artist) => matchesLibraryField(artist, q)) ||
    matchesLibraryField(item.album, q)
  )
}

export function matchesLibraryGenreName(genreName, query) {
  return matchesLibraryField(genreName, query)
}

export function matchesLibraryFilter(item, query) {
  return matchesLibraryTrackItem(item, query)
}
