import { describe, expect, it } from 'vitest'

import {
  albumLibraryStatus,
  missingAlbumTracks,
} from '../model/albumDownload.js'

describe('album download remaining', () => {
  const library = [
    {
      file: 'Artist/Album/One.flac',
      artist: 'Artist',
      album: 'Album',
      title: 'One',
    },
  ]

  it('marks a partial album as remaining', () => {
    expect(
      albumLibraryStatus(
        {
          media_type: 'album',
          name: 'Album',
          artists: ['Artist'],
          track_count: 3,
        },
        library
      )
    ).toEqual({
      kind: 'remaining',
      have: 1,
      expected: 3,
      missing: 2,
    })
  })

  it('filters owned tracks out of an album queue', () => {
    const tracks = [
      { name: 'One', artists: ['Artist'] },
      { name: 'Two', artists: ['Artist'] },
    ]
    expect(missingAlbumTracks(tracks, library).map((track) => track.name)).toEqual(
      ['Two']
    )
  })
})
