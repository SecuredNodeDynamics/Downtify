import { albumKey, groupAlbums, normalizeLibraryItem } from './library'

let pendingNavigation = null

export function setPlayerNavigation(intent) {
  pendingNavigation = intent?.file ? { ...intent } : null
}

export function consumePlayerNavigation() {
  const intent = pendingNavigation
  pendingNavigation = null
  return intent ? { ...intent } : null
}

export function canOpenHistoryInPlayer(item) {
  return (
    Boolean(item?.filename) &&
    (item.status === 'done' || item.status === 'skipped')
  )
}

export function resolvePlayerBrowseState(libraryItems, intent, options = {}) {
  const unknownArtist = options.unknownArtist || 'Unknown Artist'
  const file = String(intent?.file || '').trim()
  if (!file) return null

  const items = Array.isArray(libraryItems) ? libraryItems : []
  const albums = groupAlbums(items, { unknownArtist })

  let albumEntry = albums.find((album) => album.files.includes(file))

  const artistHint = String(intent.artist || '').trim()
  const albumHint = String(intent.album || '').trim()
  if (!albumEntry && artistHint && albumHint) {
    const key = albumKey(artistHint, albumHint)
    albumEntry = albums.find((album) => album.key === key)
  }

  if (albumEntry) {
    return {
      browseMode: 'albums',
      selectedArtistName: albumEntry.artist,
      selectedAlbumKey: albumEntry.key,
      selectedGenreName: '',
      playlistFiles: albumEntry.files,
      startFile: file,
      context: {
        type: 'album',
        name: albumEntry.name,
        artist: albumEntry.artist,
      },
    }
  }

  const normalized =
    items.find((item) => item.file === file) ||
    normalizeLibraryItem(
      { file, artist: artistHint, album: albumHint },
      { unknownArtist }
    )
  const artist = artistHint || normalized.artist

  const artistFiles = items
    .filter(
      (item) => normalizeLibraryItem(item, { unknownArtist }).artist === artist
    )
    .map((item) => item.file)

  if (artistFiles.length > 1) {
    return {
      browseMode: 'artists',
      selectedArtistName: artist,
      selectedAlbumKey: '',
      selectedGenreName: '',
      playlistFiles: artistFiles,
      startFile: file,
      context: { type: 'artist', name: artist },
    }
  }

  return {
    browseMode: 'tracks',
    selectedArtistName: '',
    selectedAlbumKey: '',
    selectedGenreName: '',
    playlistFiles: [file],
    startFile: file,
  }
}
