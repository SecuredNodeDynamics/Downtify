import { ref, computed } from 'vue'

import API from './api.js'
import {
  isSameAudioFile,
  isSameAudioUrl,
  resolvePlaybackUrl,
} from './playerAudioUrl.js'
import { recoveryDelayMs, shouldRecoverPlayback } from './playbackRecovery.js'
import {
  initPlayerMediaSession,
  syncMediaSessionMetadata,
  syncMediaSessionPlaybackState,
  syncMediaSessionPosition,
} from './playerMediaSession.js'
import { usesEmbeddedServer } from './serverConnection.js'

const VOLUME_KEY = 'downtify-player-volume'
const SESSION_KEY = 'downtify-player-session-v1'

const playlist = ref([])
const currentIndex = ref(-1)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(parseFloat(localStorage.getItem(VOLUME_KEY) || '0.85'))
const isMuted = ref(false)
const repeatMode = ref('off') // 'off' | 'all' | 'one'
const shuffle = ref(false)
const playlistContext = ref(null)

let audio = null
let shuffleOrder = []
let shufflePos = 0
let progressRaf = 0
let isSeeking = false
let playingFile = ''
// Whether the user wants audio playing right now. Distinct from `isPlaying`,
// which mirrors the element's actual play/pause state: during a network stall
// the stream is paused by the browser even though playback is still intended.
let playbackIntent = false
let recoverTimer = 0
let recoverAttempts = 0
let recovering = false
let mediaSessionReady = false
let lastMediaPositionSyncAt = 0
let lastSessionPersistAt = 0
let applyTrackSeq = 0
let pendingSession = readPlayerSession()

function readPlayerSession() {
  try {
    const parsed = JSON.parse(localStorage.getItem(SESSION_KEY) || 'null')
    if (!parsed || typeof parsed.file !== 'string' || !parsed.file) return null
    return {
      file: parsed.file,
      time: Math.max(0, Number(parsed.time) || 0),
      playing: Boolean(parsed.playing),
      repeatMode: ['off', 'all', 'one'].includes(parsed.repeatMode)
        ? parsed.repeatMode
        : 'off',
      shuffle: Boolean(parsed.shuffle),
      context:
        parsed.context && typeof parsed.context === 'object'
          ? parsed.context
          : null,
    }
  } catch {
    return null
  }
}

function persistPlayerSession(force = false) {
  const now = Date.now()
  if (!force && now - lastSessionPersistAt < 1000) return
  const track = currentTrackForMediaSession()
  if (!track?.file) return
  lastSessionPersistAt = now
  try {
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        file: track.file,
        time: audio?.currentTime || currentTime.value || 0,
        playing: playbackIntent || isPlaying.value,
        repeatMode: repeatMode.value,
        shuffle: shuffle.value,
        context: playlistContext.value,
      })
    )
  } catch {
    // Ignore private-mode storage failures.
  }
}

function restorePlayerSession(paths) {
  const session = pendingSession
  if (!session || currentIndex.value >= 0) return false
  const index = paths.indexOf(session.file)
  if (index < 0) {
    pendingSession = null
    return false
  }

  repeatMode.value = session.repeatMode
  shuffle.value = session.shuffle
  playlistContext.value = session.context
  currentIndex.value = index
  currentTime.value = session.time
  void applyTrack(index, {
    autoplay: false,
    resetTime: false,
    restoreTime: session.time,
  })
  pendingSession = null
  return true
}

function currentTrackForMediaSession() {
  return currentIndex.value >= 0 && currentIndex.value < playlist.value.length
    ? playlist.value[currentIndex.value]
    : null
}

function syncMediaSessionNow({ position = false } = {}) {
  if (!mediaSessionReady) return
  const track = currentTrackForMediaSession()
  const a = audio
  const idle = !track || (!playbackIntent && (!a || a.paused))

  void syncMediaSessionPlaybackState({
    playing: Boolean(a && !a.paused),
    paused: Boolean(a && a.paused && playbackIntent),
    idle,
  })

  if (track) {
    void syncMediaSessionMetadata(track)
  }

  if (!position || !a) return
  const now = Date.now()
  if (now - lastMediaPositionSyncAt < 1500) return
  lastMediaPositionSyncAt = now
  void syncMediaSessionPosition({
    position: a.currentTime,
    duration: duration.value || a.duration,
    playbackRate: a.playbackRate || 1,
  })
}

function resumePlaybackIfNeeded() {
  const a = audio
  if (!a || !playbackIntent || !a.paused) return
  playAudioWithRecovery(a)
}

function playAudioWithRecovery(el = audio) {
  if (!el) return Promise.resolve(false)
  return el
    .play()
    .then(() => true)
    .catch(() => {
      if (el === audio && playbackIntent) scheduleRecovery()
      return false
    })
}

async function ensureMediaSession() {
  if (mediaSessionReady) return
  await initPlayerMediaSession({
    play,
    pause,
    prev,
    next,
    seek,
    seekBy: (delta) => {
      const a = ensureAudio()
      seek((a.currentTime || 0) + delta)
    },
    onForeground: resumePlaybackIfNeeded,
  })
  mediaSessionReady = true
  syncMediaSessionNow({ position: true })
}

function isStreamedPlayback() {
  // Embedded builds play local files via the Capacitor file bridge and never
  // suffer network underruns; everything else streams over HTTP.
  return !usesEmbeddedServer()
}

function clearRecoverTimer() {
  if (recoverTimer) {
    clearTimeout(recoverTimer)
    recoverTimer = 0
  }
}

function resetRecovery() {
  recoverAttempts = 0
  recovering = false
  clearRecoverTimer()
}

function recoveryContext() {
  return {
    playbackIntent,
    streamed: isStreamedPlayback(),
    paused: audio ? audio.paused : true,
    seeking: isSeeking,
    readyState: audio ? audio.readyState : 0,
    attempts: recoverAttempts,
  }
}

function scheduleRecovery() {
  if (!audio || recoverTimer || recovering) return
  if (!shouldRecoverPlayback(recoveryContext())) return
  const delay = recoveryDelayMs(recoverAttempts)
  recoverTimer = setTimeout(() => {
    recoverTimer = 0
    void attemptRecovery()
  }, delay)
}

function attemptRecovery() {
  if (!audio || recovering) return
  if (!shouldRecoverPlayback(recoveryContext())) return

  recovering = true
  recoverAttempts += 1
  const el = audio
  const resumeAt = Number.isFinite(el.currentTime) ? el.currentTime : 0

  const finishFailure = () => {
    recovering = false
    scheduleRecovery()
  }

  const resume = () => {
    if (el !== audio) {
      recovering = false
      return
    }
    try {
      if (resumeAt > 0) {
        const dur = el.duration
        el.currentTime =
          Number.isFinite(dur) && dur > 0
            ? Math.min(resumeAt, dur - 0.25)
            : resumeAt
      }
    } catch {
      // Seeking can throw if the element isn't ready yet; play anyway.
    }
    playAudioWithRecovery(el)
      .then((played) => {
        if (!played) return
        // Success is finalized by the 'playing' listener (resetRecovery).
      })
      .catch(finishFailure)
  }

  const onLoaded = () => {
    el.removeEventListener('loadedmetadata', onLoaded)
    resume()
  }
  el.addEventListener('loadedmetadata', onLoaded, { once: true })

  // Re-fetch the stream from scratch; load() resets currentTime, hence the
  // resumeAt bookkeeping above.
  try {
    el.load()
  } catch {
    el.removeEventListener('loadedmetadata', onLoaded)
    finishFailure()
    return
  }

  // If the reload never reports metadata (dead connection), retry with back-off.
  setTimeout(() => {
    if (recovering && el === audio) {
      el.removeEventListener('loadedmetadata', onLoaded)
      finishFailure()
    }
  }, 6000)
}

function tickProgress() {
  if (audio && !audio.paused && !isSeeking) {
    currentTime.value = audio.currentTime
    progressRaf = requestAnimationFrame(tickProgress)
  } else {
    progressRaf = 0
  }
}

function startProgressTicker() {
  if (!progressRaf) {
    progressRaf = requestAnimationFrame(tickProgress)
  }
}

function stopProgressTicker() {
  if (progressRaf) {
    cancelAnimationFrame(progressRaf)
    progressRaf = 0
  }
}

function ensureAudio() {
  if (audio) return audio
  audio = new Audio()
  audio.preload = usesEmbeddedServer() ? 'auto' : 'metadata'
  audio.volume = volume.value
  audio.addEventListener('timeupdate', () => {
    if (!progressRaf && !isSeeking) {
      currentTime.value = audio.currentTime
    }
    syncMediaSessionNow({ position: true })
    persistPlayerSession()
  })
  audio.addEventListener('seeking', () => {
    isSeeking = true
  })
  audio.addEventListener('seeked', () => {
    isSeeking = false
    if (audio) currentTime.value = audio.currentTime
  })
  audio.addEventListener('loadedmetadata', () => {
    duration.value = isFinite(audio.duration) ? audio.duration : 0
  })
  audio.addEventListener('durationchange', () => {
    duration.value = isFinite(audio.duration) ? audio.duration : 0
  })
  audio.addEventListener('ended', onEnded)
  audio.addEventListener('error', () => {
    isPlaying.value = false
    stopProgressTicker()
    scheduleRecovery()
  })
  // A network underrun on a streamed source: the browser pauses to rebuffer.
  // Give it a moment to recover on its own, then reload-and-resume if not.
  audio.addEventListener('waiting', scheduleRecovery)
  audio.addEventListener('stalled', scheduleRecovery)
  audio.addEventListener('play', () => {
    isPlaying.value = true
    startProgressTicker()
    void ensureMediaSession()
    syncMediaSessionNow({ position: true })
  })
  audio.addEventListener('playing', () => {
    isPlaying.value = true
    resetRecovery()
    startProgressTicker()
    syncMediaSessionNow({ position: true })
  })
  audio.addEventListener('pause', () => {
    isPlaying.value = false
    stopProgressTicker()
    if (audio) currentTime.value = audio.currentTime
    syncMediaSessionNow({ position: true })
    persistPlayerSession(true)
  })
  return audio
}

function fileUrl(file) {
  return API.downloadFileURL(file)
}

function coverUrl(file) {
  return API.coverFileURL(file)
}

function trackFromFile(file) {
  const noExt = file.replace(/\.[^.]+$/, '')
  let artist = ''
  let title = noExt
  const dash = noExt.indexOf(' - ')
  if (dash > 0) {
    artist = noExt.slice(0, dash).trim()
    title = noExt.slice(dash + 3).trim()
  }
  return {
    file,
    url: fileUrl(file),
    cover: coverUrl(file),
    title,
    artist,
  }
}

function buildShuffleOrder() {
  const indices = playlist.value.map((_, i) => i)
  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[indices[i], indices[j]] = [indices[j], indices[i]]
  }
  shuffleOrder = indices
  shufflePos =
    currentIndex.value >= 0
      ? Math.max(0, shuffleOrder.indexOf(currentIndex.value))
      : 0
}

function selectAt(index) {
  void applyTrack(index, { autoplay: false, resetTime: false })
}

async function applyTrack(
  index,
  { autoplay = false, resetTime = true, restoreTime = 0 } = {}
) {
  if (index < 0 || index >= playlist.value.length) return
  const seq = ++applyTrackSeq
  const a = ensureAudio()
  const wasPlaying = isPlaying.value || playbackIntent
  const track = playlist.value[index]
  currentIndex.value = index
  if (shuffle.value) {
    if (shuffleOrder.length !== playlist.value.length) buildShuffleOrder()
    const pos = shuffleOrder.indexOf(index)
    if (pos >= 0) shufflePos = pos
  }
  syncMediaSessionNow({ position: true })

  const nextUrl = await resolvePlaybackUrl(track.file)
  if (seq !== applyTrackSeq || currentIndex.value !== index) return
  track.url = nextUrl

  const sameSource =
    playingFile === track.file &&
    (isSameAudioFile(a.src, track.file) || isSameAudioUrl(a.src, nextUrl))

  if (!sameSource) {
    a.pause()
    isPlaying.value = false
    stopProgressTicker()
    resetRecovery()
    playingFile = track.file
    a.src = nextUrl
    a.load()
    if (resetTime) {
      a.currentTime = 0
      currentTime.value = 0
      duration.value = 0
    }
    if (restoreTime > 0) {
      const applyRestoreTime = () => {
        if (playingFile !== track.file) return
        try {
          a.currentTime = Math.min(
            restoreTime,
            Number.isFinite(a.duration)
              ? Math.max(0, a.duration - 0.25)
              : restoreTime
          )
          currentTime.value = a.currentTime
        } catch {
          // Metadata is not ready yet; loadedmetadata will retry.
        }
      }
      a.addEventListener('loadedmetadata', applyRestoreTime, { once: true })
      applyRestoreTime()
    }
    if (autoplay || wasPlaying) {
      playbackIntent = true
      await playAudioWithRecovery(a)
    }
    return
  }

  if ((autoplay || wasPlaying) && a.paused) {
    playbackIntent = true
    await playAudioWithRecovery(a)
  }
}

export function syncPlaylistFromFiles(files, options = {}) {
  const paths = (files || []).filter(Boolean)
  if (!paths.length) return

  if (
    playlistContext.value?.type &&
    options.preserveContext !== false &&
    currentIndex.value >= 0
  ) {
    const currentFile = playlist.value[currentIndex.value]?.file
    if (currentFile && paths.includes(currentFile)) return
  }

  const currentFile =
    currentIndex.value >= 0 ? playlist.value[currentIndex.value]?.file : null

  const pathsUnchanged =
    paths.length === playlist.value.length &&
    paths.every((file, index) => playlist.value[index]?.file === file)

  if (pathsUnchanged) return

  if (currentFile && paths.includes(currentFile)) {
    const wasPlaying = isPlaying.value
    playlist.value = paths.map((file) => trackFromFile(file))
    currentIndex.value = paths.indexOf(currentFile)
    if (shuffle.value) buildShuffleOrder()

    const track = playlist.value[currentIndex.value]
    const a = ensureAudio()
    if (track && !isSameAudioFile(a.src, track.file)) {
      selectAt(currentIndex.value)
      return
    }
    if (wasPlaying && a.paused) {
      playbackIntent = true
      playAudioWithRecovery(a)
    }
    return
  }

  if (currentFile && !paths.includes(currentFile)) {
    pause()
    currentIndex.value = -1
  }

  setPlaylist(paths, options)
}

function setPlaylist(files, options = {}) {
  const tracks = (files || []).map((f) =>
    typeof f === 'string' ? trackFromFile(f) : f
  )
  playlist.value = tracks
  playlistContext.value = options.context || null
  if (restorePlayerSession(tracks.map((track) => track.file))) {
    if (shuffle.value) buildShuffleOrder()
    return
  }
  if (currentIndex.value >= tracks.length) currentIndex.value = -1
  if (shuffle.value) buildShuffleOrder()
  if (typeof options.startIndex === 'number') {
    if (options.autoplay === false) {
      selectAt(options.startIndex)
    } else {
      playAt(options.startIndex)
    }
  } else if (
    options.selectFirst &&
    tracks.length > 0 &&
    currentIndex.value < 0
  ) {
    selectAt(0)
  } else if (options.autoplay && tracks.length > 0 && currentIndex.value < 0) {
    playAt(0)
  }
}

function playAt(index) {
  void applyTrack(index, { autoplay: true, resetTime: true })
}

function play() {
  if (playlist.value.length === 0) return
  void ensureMediaSession()
  const a = ensureAudio()
  if (currentIndex.value < 0) {
    playAt(0)
    return
  }
  const track = playlist.value[currentIndex.value]
  if (!track) return
  if (!a.src || !isSameAudioFile(a.src, track.file)) {
    void applyTrack(currentIndex.value, { autoplay: true, resetTime: false })
    return
  }
  playbackIntent = true
  playAudioWithRecovery(a)
}

function pause() {
  playbackIntent = false
  resetRecovery()
  if (audio) audio.pause()
  persistPlayerSession(true)
}

function toggle() {
  if (isPlaying.value) pause()
  else play()
}

function seek(seconds) {
  const a = ensureAudio()
  const max = duration.value || 0
  const clamped = Math.max(0, Math.min(max, seconds))
  isSeeking = true
  a.currentTime = clamped
  currentTime.value = clamped
  lastMediaPositionSyncAt = 0
  syncMediaSessionNow({ position: true })
}

function seekRatio(ratio) {
  if (!duration.value) return
  seek(duration.value * Math.max(0, Math.min(1, ratio)))
}

function setVolume(v) {
  const clamped = Math.max(0, Math.min(1, v))
  volume.value = clamped
  if (audio) audio.volume = clamped
  try {
    localStorage.setItem(VOLUME_KEY, String(clamped))
  } catch {
    // ignore
  }
  if (clamped > 0 && isMuted.value) {
    isMuted.value = false
    if (audio) audio.muted = false
  }
}

function toggleMute() {
  isMuted.value = !isMuted.value
  if (audio) audio.muted = isMuted.value
}

function nextIndex() {
  if (playlist.value.length === 0) return -1
  if (shuffle.value) {
    if (shuffleOrder.length !== playlist.value.length) buildShuffleOrder()
    const nextPos = (shufflePos + 1) % shuffleOrder.length
    return shuffleOrder[nextPos]
  }
  const i = currentIndex.value + 1
  if (i >= playlist.value.length) {
    return repeatMode.value === 'all' ? 0 : -1
  }
  return i
}

function prevIndex() {
  if (playlist.value.length === 0) return -1
  if (shuffle.value) {
    if (shuffleOrder.length !== playlist.value.length) buildShuffleOrder()
    const prevPos = (shufflePos - 1 + shuffleOrder.length) % shuffleOrder.length
    return shuffleOrder[prevPos]
  }
  const i = currentIndex.value - 1
  if (i < 0) {
    return repeatMode.value === 'all' ? playlist.value.length - 1 : 0
  }
  return i
}

function next() {
  const i = nextIndex()
  if (i < 0) {
    pause()
    return
  }
  playAt(i)
}

function prev() {
  const a = ensureAudio()
  if (a.currentTime > 3) {
    seek(0)
    return
  }
  const i = prevIndex()
  if (i < 0) return
  playAt(i)
}

function onEnded() {
  if (repeatMode.value === 'one') {
    seek(0)
    if (audio) {
      playbackIntent = true
      playAudioWithRecovery(audio)
    }
    return
  }
  next()
}

function setRepeat(mode) {
  if (['off', 'all', 'one'].includes(mode)) {
    repeatMode.value = mode
    persistPlayerSession(true)
  }
}

function cycleRepeat() {
  const order = ['off', 'all', 'one']
  const i = order.indexOf(repeatMode.value)
  setRepeat(order[(i + 1) % order.length])
}

function setShuffle(v) {
  shuffle.value = !!v
  if (shuffle.value) buildShuffleOrder()
  persistPlayerSession(true)
}

function toggleShuffle() {
  setShuffle(!shuffle.value)
}

const currentTrack = computed(() =>
  currentIndex.value >= 0 && currentIndex.value < playlist.value.length
    ? playlist.value[currentIndex.value]
    : null
)

const progressPct = computed(() =>
  duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
)

const upNext = computed(() => {
  const list = playlist.value
  const index = currentIndex.value
  if (index < 0 || list.length <= 1) return []
  const limit = Math.min(12, list.length - 1)
  const result = []

  if (shuffle.value) {
    if (shuffleOrder.length !== list.length) buildShuffleOrder()
    const startPos = shuffleOrder.indexOf(index)
    if (startPos < 0) return []
    for (let step = 1; step <= limit; step += 1) {
      const pos = startPos + step
      if (pos >= shuffleOrder.length && repeatMode.value !== 'all') break
      const nextIndex = shuffleOrder[pos % shuffleOrder.length]
      if (nextIndex === index) break
      result.push({
        track: list[nextIndex],
        index: nextIndex,
        offset: result.length + 1,
      })
    }
    return result
  }

  for (let step = 1; step <= limit; step += 1) {
    let nextIndex = index + step
    if (nextIndex >= list.length) {
      if (repeatMode.value !== 'all') break
      nextIndex %= list.length
    }
    if (nextIndex === index) break
    result.push({
      track: list[nextIndex],
      index: nextIndex,
      offset: result.length + 1,
    })
  }
  return result
})

if (typeof window !== 'undefined') {
  window.addEventListener('pagehide', () => persistPlayerSession(true))
}

export function formatTime(seconds) {
  if (!isFinite(seconds) || seconds < 0) return '0:00'
  const total = Math.floor(seconds)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function trackInfoFromFile(file) {
  return trackFromFile(file)
}

export function usePlayer() {
  return {
    playlist,
    playlistContext,
    currentIndex,
    currentTrack,
    upNext,
    isPlaying,
    currentTime,
    duration,
    progressPct,
    volume,
    isMuted,
    repeatMode,
    shuffle,
    setPlaylist,
    syncPlaylistFromFiles,
    selectAt,
    playAt,
    play,
    pause,
    toggle,
    seek,
    seekRatio,
    setVolume,
    toggleMute,
    next,
    prev,
    setRepeat,
    cycleRepeat,
    setShuffle,
    toggleShuffle,
  }
}
