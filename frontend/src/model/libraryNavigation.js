import { albumKey, libraryItemArtists } from './library'

let pendingLibraryNavigation = null

export function setLibraryNavigation(intent) {
  pendingLibraryNavigation = intent ? { ...intent } : null
}

export function consumeLibraryNavigation() {
  const intent = pendingLibraryNavigation
  pendingLibraryNavigation = null
  return intent ? { ...intent } : null
}

export function libraryNavigationForAlbum(album) {
  if (!album?.key) return null
  return {
    browseMode: 'albums',
    selectedArtistName: album.artist || '',
    selectedAlbumKey: album.key,
    selectedGenreName: '',
  }
}

export function libraryNavigationForTrack(track, options = {}) {
  if (!track?.file) return null
  const preferredArtist = String(options.preferredArtist || '').trim()
  const creditedArtists = libraryItemArtists(track)
  const artist =
    (preferredArtist &&
      creditedArtists.find(
        (name) => name.toLowerCase() === preferredArtist.toLowerCase()
      )) ||
    creditedArtists[0] ||
    String(track.artist || '').trim()
  const album = String(track.album || '').trim()
  if (album && artist) {
    return {
      browseMode: 'albums',
      selectedArtistName: artist,
      selectedAlbumKey: albumKey(artist, album),
      selectedGenreName: '',
      highlightFile: track.file,
    }
  }
  return {
    browseMode: 'tracks',
    selectedArtistName: '',
    selectedAlbumKey: '',
    selectedGenreName: '',
    highlightFile: track.file,
  }
}
