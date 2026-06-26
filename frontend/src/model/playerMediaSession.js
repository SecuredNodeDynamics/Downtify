import { MediaSession } from '@capgo/capacitor-media-session'
import { App } from '@capacitor/app'

import { isCapacitorNative } from './serverConnection.js'

let initialized = false
let resumeListener = null

export function mediaSessionPlaybackState({ playing, paused, idle }) {
  if (idle) return 'none'
  if (playing) return 'playing'
  if (paused) return 'paused'
  return 'none'
}

export function artworkSourcesForTrack(track) {
  const src = String(track?.cover || '').trim()
  if (!src || src.startsWith('blob:')) return []
  return [{ src, sizes: '512x512', type: 'image/jpeg' }]
}

export async function initPlayerMediaSession(handlers = {}) {
  if (!isCapacitorNative() || initialized) return
  initialized = true

  const call = (name) => () => {
    const fn = handlers[name]
    if (typeof fn === 'function') fn()
  }

  await MediaSession.setActionHandler({ action: 'play' }, call('play'))
  await MediaSession.setActionHandler({ action: 'pause' }, call('pause'))
  await MediaSession.setActionHandler({ action: 'previoustrack' }, call('prev'))
  await MediaSession.setActionHandler({ action: 'nexttrack' }, call('next'))
  await MediaSession.setActionHandler({ action: 'seekbackward' }, () => {
    handlers.seekBy?.(-15)
  })
  await MediaSession.setActionHandler({ action: 'seekforward' }, () => {
    handlers.seekBy?.(15)
  })
  await MediaSession.setActionHandler({ action: 'seekto' }, (details) => {
    const seekTime = Number(details?.seekTime)
    if (Number.isFinite(seekTime)) handlers.seek?.(seekTime)
  })
  await MediaSession.setActionHandler({ action: 'stop' }, call('pause'))

  resumeListener = await App.addListener('appStateChange', ({ isActive }) => {
    if (isActive) handlers.onForeground?.()
  })
}

export async function clearPlayerMediaSession() {
  if (resumeListener) {
    await resumeListener.remove()
    resumeListener = null
  }
  initialized = false
}

export async function syncMediaSessionMetadata(track) {
  if (!isCapacitorNative() || !track) return

  await MediaSession.setMetadata({
    title: track.title || 'Unknown title',
    artist: track.artist || 'Unknown artist',
    album: track.album || '',
    artwork: artworkSourcesForTrack(track),
  })
}

export async function syncMediaSessionPlaybackState(state) {
  if (!isCapacitorNative()) return
  const playbackState = mediaSessionPlaybackState(state)
  await MediaSession.setPlaybackState({ playbackState })
}

export async function syncMediaSessionPosition({
  position = 0,
  duration = 0,
  playbackRate = 1,
} = {}) {
  if (!isCapacitorNative()) return

  const safeDuration = Number.isFinite(duration) && duration > 0 ? duration : 0
  const safePosition =
    Number.isFinite(position) && position >= 0
      ? Math.min(position, safeDuration || position)
      : 0

  await MediaSession.setPositionState({
    position: safePosition,
    duration: safeDuration,
    playbackRate: playbackRate || 1,
  })
}
