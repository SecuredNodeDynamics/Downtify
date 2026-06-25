import { describe, expect, it } from 'vitest'

import { groupAlbums } from '../model/library'
import {
  consumeLibraryNavigation,
  libraryNavigationForAlbum,
  libraryNavigationForTrack,
  setLibraryNavigation,
} from '../model/libraryNavigation'
import { findOwnedAlbum } from '../model/libraryOwnership'

describe('libraryNavigation', () => {
  it('stores and consumes pending library navigation once', () => {
    setLibraryNavigation({
      browseMode: 'albums',
      selectedArtistName: 'Artist',
      selectedAlbumKey: 'Artist\u0000Album',
      selectedGenreName: '',
    })
    expect(consumeLibraryNavigation()).toEqual({
      browseMode: 'albums',
      selectedArtistName: 'Artist',
      selectedAlbumKey: 'Artist\u0000Album',
      selectedGenreName: '',
    })
    expect(consumeLibraryNavigation()).toBeNull()
  })

  it('finds owned albums for library navigation', () => {
    const libraryItems = [
      {
        file: 'Swing Nation Music/Born to Swing/01.flac',
        artist: 'Swing Nation Music',
        album: 'Born to Swing',
        title: 'Born to Swing',
      },
    ]
    const album = findOwnedAlbum(
      {
        media_type: 'album',
        name: 'Born to Swing',
        artists: ['Swing Nation Music'],
      },
      libraryItems
    )

    expect(album?.name).toBe('Born to Swing')
    expect(libraryNavigationForAlbum(album)).toEqual({
      browseMode: 'albums',
      selectedArtistName: 'Swing Nation Music',
      selectedAlbumKey: groupAlbums(libraryItems)[0].key,
      selectedGenreName: '',
    })
  })

  it('navigates collab tracks under the preferred credited artist', () => {
    const track = {
      file: 'Connor Price/Swing/Swing.flac',
      artist: 'Connor Price',
      artists: ['Connor Price', 'Nic D'],
      album: 'Swing',
      title: 'Swing',
    }

    expect(
      libraryNavigationForTrack(track, { preferredArtist: 'Nic D' })
    ).toEqual({
      browseMode: 'albums',
      selectedArtistName: 'Nic D',
      selectedAlbumKey: 'Nic D\u0000Swing',
      selectedGenreName: '',
      highlightFile: 'Connor Price/Swing/Swing.flac',
    })
  })
})
