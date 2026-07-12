import { ref, unref, watch } from 'vue'

import API from './api'
import {
  normalizeLibraryItem,
  groupAlbums,
  libraryItemArtists,
} from './library'
import { getCachedLibraryItems, onLibraryChanged } from './librarySession'

export function mediaItemKey(item) {
  return String(item?.song_id || item?.browse_id || item?.url || '')
}

function normalizeDupKey(text) {
  return String(text || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '')
}

function artistKeys(item) {
  const keys = new Set()
  for (const artist of item?.artists || []) {
    const key = normalizeDupKey(artist)
    if (key) keys.add(key)
  }
  const combined = String(item?.artist || '').trim()
  if (combined) {
    for (const part of combined.split(/[,/&]+/)) {
      const key = normalizeDupKey(part)
      if (key) keys.add(key)
    }
  }
  return keys
}

function artistKeysMatch(searchKeys, libraryArtist) {
  if (!searchKeys.size) return true
  const itemKey = normalizeDupKey(libraryArtist)
  if (!itemKey) return false
  if (searchKeys.has(itemKey)) return true
  for (const key of searchKeys) {
    if (key && itemKey && (key.includes(itemKey) || itemKey.includes(key))) {
      return true
    }
  }
  return false
}

export function isMediaOwnedLocally(item, libraryItems) {
  if (!item || !Array.isArray(libraryItems) || !libraryItems.length) {
    return false
  }
  return Boolean(
    findOwnedAlbum(item, libraryItems) || findOwnedTrack(item, libraryItems)
  )
}

export function findOwnedAlbum(item, libraryItems) {
  if (!item || !Array.isArray(libraryItems) || !libraryItems.length) {
    return null
  }
  if (item.media_type && item.media_type !== 'album') return null

  const albums = groupAlbums(libraryItems, { unknownArtist: 'Unknown Artist' })
  const albumNameKey = normalizeDupKey(item.name || item.album_name)
  if (!albumNameKey) return null

  const searchArtists = artistKeys(item)
  const matches = []
  for (const album of albums) {
    if (normalizeDupKey(album.name) !== albumNameKey) continue
    matches.push(album)
  }
  for (const album of matches) {
    if (!artistKeysMatch(searchArtists, album.artist)) continue
    if (albumHasExpectedTrackCount(item, album)) return album
  }
  const fallback = matches.find((album) =>
    albumHasExpectedTrackCount(item, album)
  )
  return fallback || null
}

function expectedAlbumTrackCount(item) {
  for (const field of [
    'track_count',
    'album_track_total',
    'tracks_count',
    'total_tracks',
  ]) {
    const count = Number(item?.[field])
    if (Number.isFinite(count) && count > 0) return count
  }
  return Array.isArray(item?.tracks) ? item.tracks.length : 0
}

function albumHasExpectedTrackCount(item, album) {
  const expected = expectedAlbumTrackCount(item)
  if (!expected) return true
  const have = Array.isArray(album?.files) ? album.files.length : 0
  return have >= expected
}

export function findOwnedTrack(item, libraryItems) {
  if (!item || !Array.isArray(libraryItems) || !libraryItems.length) {
    return null
  }

  const titleKey = normalizeDupKey(item.name)
  if (!titleKey) return null
  const searchArtists = artistKeys(item)

  for (const raw of libraryItems) {
    const lib = normalizeLibraryItem(raw)
    if (normalizeDupKey(lib.title) !== titleKey) continue
    let matched = false
    for (const libArtist of libraryItemArtists(lib)) {
      if (artistKeysMatch(searchArtists, libArtist)) {
        matched = true
        break
      }
    }
    if (!matched) continue
    return lib
  }
  return null
}

function resolveSource(source) {
  const raw = unref(source)
  if (typeof raw === 'function') return raw()
  return raw
}

export function useLibraryOwnership(itemsSource) {
  const ownedKeys = ref(new Set())
  let requestId = 0

  function applyLocalOwnership(items) {
    const libraryItems = getCachedLibraryItems()
    if (!libraryItems?.length) return
    const next = new Set(ownedKeys.value)
    for (const item of items || []) {
      const key = mediaItemKey(item)
      if (!key) continue
      if (isMediaOwnedLocally(item, libraryItems)) {
        next.add(key)
      }
    }
    ownedKeys.value = next
  }

  async function refresh(items) {
    const list = (items || []).filter((item) => mediaItemKey(item))
    if (!list.length) {
      ownedKeys.value = new Set()
      return
    }

    applyLocalOwnership(list)

    const id = ++requestId
    try {
      const res = await API.checkLibraryOwned(list)
      if (id !== requestId) return
      const map = res.data?.owned || {}
      const next = new Set(ownedKeys.value)
      for (const [key, owned] of Object.entries(map)) {
        if (owned) next.add(key)
        else next.delete(key)
      }
      ownedKeys.value = next
    } catch {
      if (id !== requestId) return
    }
  }

  watch(
    () => resolveSource(itemsSource),
    (items) => {
      void refresh(items)
    },
    { immediate: true, deep: true }
  )

  onLibraryChanged(() => {
    const items = resolveSource(itemsSource)
    if (items?.length) applyLocalOwnership(items)
  })

  function isOwned(item) {
    if (!item) return false
    return ownedKeys.value.has(mediaItemKey(item))
  }

  return { ownedKeys, isOwned, refresh }
}

export async function isMediaOwned(item) {
  const key = mediaItemKey(item)
  if (!key) return false

  const libraryItems = getCachedLibraryItems()
  if (libraryItems?.length && isMediaOwnedLocally(item, libraryItems)) {
    return true
  }

  try {
    const res = await API.checkLibraryOwned([item])
    return Boolean(res.data?.owned?.[key])
  } catch {
    return false
  }
}
