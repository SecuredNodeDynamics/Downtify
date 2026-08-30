import {
  albumHasExpectedTrackCount,
  expectedAlbumTrackCount,
  findLibraryAlbum,
  findOwnedTrack,
} from './libraryOwnership'

export function albumLibraryStatus(item, libraryItems) {
  const album = findLibraryAlbum(item, libraryItems)
  const have = Array.isArray(album?.files) ? album.files.length : 0
  const expected = expectedAlbumTrackCount(item)
  if (!album || have < 1) {
    return {
      kind: 'download',
      have: 0,
      expected,
      missing: expected || 0,
    }
  }
  if (albumHasExpectedTrackCount(item, album)) {
    return { kind: 'owned', have, expected, missing: 0 }
  }
  return {
    kind: 'remaining',
    have,
    expected,
    missing: expected ? Math.max(0, expected - have) : 0,
  }
}

export function missingAlbumTracks(tracks, libraryItems) {
  const list = Array.isArray(tracks) ? tracks : []
  if (!list.length) return []
  const library = Array.isArray(libraryItems) ? libraryItems : []
  if (!library.length) return list
  return list.filter((track) => !findOwnedTrack(track, library))
}
