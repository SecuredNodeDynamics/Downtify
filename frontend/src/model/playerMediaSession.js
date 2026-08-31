import { MediaSession } from '@capgo/capacitor-media-session'
import { App } from '@capacitor/app'

import { isCapacitorNative } from './serverConnection.js'

const WEB_MEDIA_ACTIONS = [
  'play',
  'pause',
  'previoustrack',
  'nexttrack',
  'seekbackward',
  'seekforward',
  'seekto',
  'stop',
]

let initialized = false
let resumeListener = null
let usingWebSession = false

export function mediaSessionPlaybackState({ playing, paused, idle }) {
  if (playing) return 'playing'
  if (paused) return 'paused'
  if (idle) return 'none'
  return 'paused'
}

export function createHeadsetClickRouter({
  toggle,
  next,
  previous,
  windowMs = 420,
} = {}) {
  let count = 0
  let timer = 0

  function flush() {
    const n = count
    count = 0
    timer = 0
    if (n >= 3) previous?.()
    else if (n === 2) next?.()
    else toggle?.()
  }

  function cancel() {
    if (timer) clearTimeout(timer)
    timer = 0
    count = 0
  }

  function onPlayPause() {
    count += 1
    if (timer) clearTimeout(timer)
    timer = setTimeout(flush, windowMs)
  }

  return { onPlayPause, cancel }
}

export function artworkSourcesForTrack(track) {
  const src = String(track?.cover || '').trim()
  if (!src || src.startsWith('blob:')) return []
  return [{ src, sizes: '512x512', type: 'image/jpeg' }]
}

function webMediaSession() {
  return typeof navigator !== 'undefined' ? navigator.mediaSession : null
}

function bindWebAction(session, action, handler) {
  try {
    session.setActionHandler(action, handler)
  } catch {
    // Older browsers reject unsupported Media Session actions.
  }
}

export async function initPlayerMediaSession(handlers = {}) {
  if (initialized) return

  const headset = createHeadsetClickRouter({
    toggle: () => handlers.toggle?.(),
    next: () => handlers.next?.(),
    previous: () => {
      if (typeof handlers.previous === 'function') handlers.previous()
      else handlers.prev?.()
    },
  })
  const call = (name) => () => {
    headset.cancel()
    const fn = handlers[name]
    if (typeof fn === 'function') fn()
  }

  if (isCapacitorNative()) {
    initialized = true
    usingWebSession = false
    await MediaSession.setActionHandler({ action: 'play' }, headset.onPlayPause)
    await MediaSession.setActionHandler(
      { action: 'pause' },
      headset.onPlayPause
    )
    await MediaSession.setActionHandler(
      { action: 'previoustrack' },
      call('previous')
    )
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
    return
  }

  const session = webMediaSession()
  if (!session) return
  initialized = true
  usingWebSession = true
  bindWebAction(session, 'play', headset.onPlayPause)
  bindWebAction(session, 'pause', headset.onPlayPause)
  bindWebAction(session, 'previoustrack', call('previous'))
  bindWebAction(session, 'nexttrack', call('next'))
  bindWebAction(session, 'seekbackward', () => handlers.seekBy?.(-15))
  bindWebAction(session, 'seekforward', () => handlers.seekBy?.(15))
  bindWebAction(session, 'seekto', (details) => {
    const seekTime = Number(details?.seekTime)
    if (Number.isFinite(seekTime)) handlers.seek?.(seekTime)
  })
  bindWebAction(session, 'stop', call('pause'))
}

export async function clearPlayerMediaSession() {
  if (resumeListener) {
    await resumeListener.remove()
    resumeListener = null
  }
  if (usingWebSession) {
    const session = webMediaSession()
    if (session) {
      for (const action of WEB_MEDIA_ACTIONS) {
        bindWebAction(session, action, null)
      }
    }
  }
  usingWebSession = false
  initialized = false
}

function metadataPayload(track) {
  return {
    title: track.title || 'Unknown title',
    artist: track.artist || 'Unknown artist',
    album: track.album || '',
    artwork: artworkSourcesForTrack(track),
  }
}

export async function syncMediaSessionMetadata(track) {
  if (!track) return
  const payload = metadataPayload(track)
  if (isCapacitorNative()) {
    await MediaSession.setMetadata(payload)
    return
  }
  const session = webMediaSession()
  if (!session || typeof MediaMetadata === 'undefined') return
  try {
    session.metadata = new MediaMetadata(payload)
  } catch {
    // Some browsers reject remote artwork URLs.
  }
}

export async function syncMediaSessionPlaybackState(state) {
  const playbackState = mediaSessionPlaybackState(state)
  if (isCapacitorNative()) {
    await MediaSession.setPlaybackState({ playbackState })
    return
  }
  const session = webMediaSession()
  if (!session) return
  session.playbackState = playbackState
}

export async function syncMediaSessionPosition({
  position = 0,
  duration = 0,
  playbackRate = 1,
} = {}) {
  const safeDuration = Number.isFinite(duration) && duration > 0 ? duration : 0
  const safePosition =
    Number.isFinite(position) && position >= 0
      ? Math.min(position, safeDuration || position)
      : 0
  const payload = {
    position: safePosition,
    duration: safeDuration,
    playbackRate: playbackRate || 1,
  }
  if (isCapacitorNative()) {
    await MediaSession.setPositionState(payload)
    return
  }
  const session = webMediaSession()
  if (!session || typeof session.setPositionState !== 'function') return
  if (!safeDuration) return
  try {
    session.setPositionState(payload)
  } catch {
    // Chrome throws when duration is still unknown.
  }
}
