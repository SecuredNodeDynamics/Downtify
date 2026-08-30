import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => false),
    isPluginAvailable: vi.fn(() => false),
  },
}))

import {
  loadProfileBundle,
  profileBundleKey,
  storeProfileBundle,
} from '../model/profileSync.js'

describe('profileSync', () => {
  const storage = {}

  afterEach(() => {
    for (const key of Object.keys(storage)) delete storage[key]
  })

  it('stores and loads a monitor bundle by profile key and username', () => {
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value
      },
      removeItem: (key) => {
        delete storage[key]
      },
    })
    const bundle = {
      profile_key: '11111111-1111-4111-8111-111111111111',
      username: 'Artyom',
      display_name: 'Artyom',
      monitors: [
        {
          spotify_id: 'pl1',
          kind: 'playlist',
          name: 'Hits',
          url: 'https://open.spotify.com/playlist/pl1',
        },
      ],
    }
    storeProfileBundle(bundle)
    expect(profileBundleKey(bundle)).toBe(
      'downtify-profile-bundle:key:11111111-1111-4111-8111-111111111111'
    )
    expect(loadProfileBundle({ username: 'artyom' }).monitors).toHaveLength(1)
    expect(
      loadProfileBundle({
        profile_key: '11111111-1111-4111-8111-111111111111',
      }).username
    ).toBe('Artyom')
  })
})
