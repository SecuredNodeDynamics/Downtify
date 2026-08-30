import { ref, computed } from 'vue'

import API from './api.js'
import {
  isCapacitorFilePlaybackUrl,
  isSameAudioFile,
  isSameAudioUrl,
  playbackHttpFallbackUrl,
  resolvePlaybackUrl,
} from './playerAudioUrl.js'
import {
  clampedSeekSeconds,
  recoveryDelayMs,
  seekWouldMove,
  shouldRecoverOnPause,
  shouldRecoverPlayback,
} from './playbackRecovery.js'
import {
  initPlayerMediaSession,
  syncMediaSessionMetadata,
  syncMediaSessionPlaybackState,
  syncMediaSessionPosition,
} from './playerMediaSession.js'
import { usesEmbeddedServer } from './serverConnection.js'
import { getCachedLibraryItems } from './librarySession.js'
import { groupAlbums } from './library.js'
import {
  enrichTrackFromLibrary,
  filesWithFollowOnAlbum,
  nextAlbumAfter,
  nextIndexInOrder,
  prevIndexInOrder,
} from './playerQueue.js'

const VOLUME_KEY = 'downtify-player-volume'
const SESSION_KEY = 'downtify-player-session-v1'
const SLOW_PLAYBACK_MS = 1500
const PLAYBACK_START_WATCHDOG_MS = 7000

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
const playbackIntent = ref(false)
let recoverTimer = 0
let playbackWatchdogTimer = 0
let recoverAttempts = 0
let recoverGeneration = 0
let recovering = false
let seekClearTimer = 0
let mediaSessionReady = false
let lastMediaPositionSyncAt = 0
let lastSessionPersistAt = 0
let applyTrackSeq = 0
let changingTrack = false
let pendingSession = readPlayerSession()
let httpFallbackTriedFor = ''

function setPlaybackIntent(value) {
  playbackIntent.value = Boolean(value)
}

function beginTrackChange() {
  changingTrack = true
  resetRecovery()
}

function endTrackChange() {
  changingTrack = false
}

function clearSeekLock() {
  isSeeking = false
  if (seekClearTimer) {
    clearTimeout(seekClearTimer)
    seekClearTimer = 0
  }
}

function nowMs() {
  return typeof performance !== 'undefined' && performance.now
    ? performance.now()
    : Date.now()
}

function logSlowPlayback(stage, startedAt, track, extra = {}) {
  const elapsed = Math.round(nowMs() - startedAt)
  if (elapsed < SLOW_PLAYBACK_MS) return
  console.warn('[Downtify player] slow playback', {
    stage,
    elapsedMs: elapsed,
    file: track?.file || '',
    ...extra,
  })
}

function preloadPlaybackUrlAt(index) {
  const track = playlist.value[index]
  if (!track?.file || track.url) return
  resolvePlaybackUrl(track.file)
    .then((url) => {
      if (url && playlist.value[index]?.file === track.file) {
        playlist.value[index].url = url
      }
    })
    .catch(() => {})
}

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
        playing: playbackIntent.value || isPlaying.value,
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
    autoplay: session.playing,
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
  const idle = !track || (!playbackIntent.value && (!a || a.paused))

  void syncMediaSessionPlaybackState({
    playing: Boolean(a && !a.paused),
    paused: Boolean(a && a.paused && playbackIntent.value),
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
  if (!a || !playbackIntent.value || !a.paused) return
  playAudioWithRecovery(a)
}

function playAudioWithRecovery(el = audio) {
  if (!el) return Promise.resolve(false)
  armPlaybackStartWatchdog(el)
  return el
    .play()
    .then(() => true)
    .catch((err) => {
      if (err?.name === 'AbortError') return false
      if (err?.name === 'NotAllowedError') {
        setPlaybackIntent(false)
        isPlaying.value = false
        persistPlayerSession(true)
        return false
      }
      if (changingTrack) return false
      if (el === audio && playbackIntent.value) {
        void switchToHttpPlaybackFallback().then((switched) => {
          if (!switched) scheduleRecovery()
        })
      }
      return false
    })
}

async function switchToHttpPlaybackFallback() {
  if (!audio || !playbackIntent.value) return false
  const track = playlist.value[currentIndex.value]
  const file = track?.file || playingFile
  if (!file || httpFallbackTriedFor === file) return false
  if (!isCapacitorFilePlaybackUrl(audio.src)) return false
  const fallback = playbackHttpFallbackUrl(file)
  if (!fallback || isSameAudioUrl(audio.src, fallback)) return false
  httpFallbackTriedFor = file
  const resumeAt = Number.isFinite(audio.currentTime) ? audio.currentTime : 0
  audio.src = fallback
  if (track) track.url = fallback
  audio.load()
  if (resumeAt > 0) {
    audio.addEventListener(
      'loadedmetadata',
      () => {
        try {
          audio.currentTime = resumeAt
        } catch {
          // Metadata may not be ready yet.
        }
      },
      { once: true }
    )
  }
  return playAudioWithRecovery(audio)
}

function clearPlaybackStartWatchdog() {
  if (playbackWatchdogTimer) {
    clearTimeout(playbackWatchdogTimer)
    playbackWatchdogTimer = 0
  }
}

function armPlaybackStartWatchdog(el = audio) {
  clearPlaybackStartWatchdog()
  if (!el || !playbackIntent.value) return
  const file = playingFile
  const startedAt = nowMs()
  const startTime = Number.isFinite(el.currentTime) ? el.currentTime : 0
  playbackWatchdogTimer = setTimeout(() => {
    playbackWatchdogTimer = 0
    if (
      el !== audio ||
      !playbackIntent.value ||
      isSeeking ||
      playingFile !== file
    ) {
      return
    }
    const current = Number.isFinite(el.currentTime) ? el.currentTime : 0
    const advanced = current > startTime + 0.25
    const hasMetadata =
      Number.isFinite(el.duration) && el.duration > 0 && el.readyState >= 1
    const healthy = advanced || (hasMetadata && el.readyState >= 3)
    if (healthy) return

    logSlowPlayback('watchdog-recovery', startedAt, currentTrack.value, {
      readyState: el.readyState,
      networkState: el.networkState,
      currentTime: current,
      duration: Number.isFinite(el.duration) ? el.duration : 0,
    })
    void switchToHttpPlaybackFallback().then((switched) => {
      if (!switched) scheduleRecovery({ force: true })
    })
  }, PLAYBACK_START_WATCHDOG_MS)
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
  // Capacitor file-bridge URLs are local. Loopback HTTP (and remote servers)
  // can stall and should use stream recovery.
  if (audio?.src && isCapacitorFilePlaybackUrl(audio.src)) return false
  if (usesEmbeddedServer() && audio?.src) return true
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
  recoverGeneration += 1
  clearRecoverTimer()
  clearPlaybackStartWatchdog()
}

function recoveryContext({ force = false } = {}) {
  return {
    playbackIntent: playbackIntent.value,
    streamed: force || isStreamedPlayback(),
    paused: audio ? audio.paused : true,
    seeking: isSeeking,
    readyState: audio ? audio.readyState : 0,
    attempts: recoverAttempts,
    changingTrack,
    force,
  }
}

function scheduleRecovery(options = {}) {
  if (!audio || recoverTimer || recovering) return
  if (!shouldRecoverPlayback(recoveryContext(options))) return
  const delay = recoveryDelayMs(recoverAttempts)
  recoverTimer = setTimeout(() => {
    recoverTimer = 0
    void attemptRecovery(options)
  }, delay)
}

function attemptRecovery(options = {}) {
  if (!audio || recovering) return
  if (!shouldRecoverPlayback(recoveryContext(options))) return

  const gen = recoverGeneration
  recovering = true
  recoverAttempts += 1
  const el = audio
  const resumeAt = Number.isFinite(el.currentTime) ? el.currentTime : 0

  const stillCurrent = () =>
    gen === recoverGeneration && el === audio && playbackIntent.value

  const finishFailure = () => {
    if (gen !== recoverGeneration) return
    recovering = false
    scheduleRecovery(options)
  }

  const resume = () => {
    if (!stillCurrent()) {
      if (gen === recoverGeneration) recovering = false
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
    if (!stillCurrent()) return
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
    if (gen !== recoverGeneration) return
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
    clearSeekLock()
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
    if (changingTrack) return
    void switchToHttpPlaybackFallback().then((switched) => {
      if (!switched) scheduleRecovery()
    })
  })
  // A network underrun on a streamed source: the browser pauses to rebuffer.
  // Give it a moment to recover on its own, then reload-and-resume if not.
  const onBufferStall = () => {
    if (changingTrack) return
    scheduleRecovery()
  }
  audio.addEventListener('waiting', onBufferStall)
  audio.addEventListener('stalled', onBufferStall)
  audio.addEventListener('play', () => {
    isPlaying.value = true
    startProgressTicker()
    void ensureMediaSession()
    syncMediaSessionNow({ position: true })
  })
  audio.addEventListener('playing', () => {
    isPlaying.value = true
    endTrackChange()
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
    if (
      shouldRecoverOnPause({
        playbackIntent: playbackIntent.value,
        changingTrack,
      })
    ) {
      scheduleRecovery()
    }
  })
  return audio
}

function fileUrl(file) {
  return API.downloadFileURL(file)
}

function coverUrl(file) {
  return API.coverFileURL(file)
}

function libraryMetaByFile() {
  const map = new Map()
  for (const item of getCachedLibraryItems() || []) {
    const file = item?.file
    if (file && !map.has(file)) map.set(file, item)
  }
  return map
}

function trackFromFile(file, metaByFile) {
  const meta = (metaByFile || libraryMetaByFile()).get(file)
  const display = enrichTrackFromLibrary(file, meta)
  return {
    file,
    url: fileUrl(file),
    cover: coverUrl(file),
    title: display.title,
    artist: display.artist,
    album: display.album,
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
  const wasPlaying = isPlaying.value || playbackIntent.value
  const track = playlist.value[index]
  currentIndex.value = index
  if (shuffle.value) {
    if (shuffleOrder.length !== playlist.value.length) buildShuffleOrder()
    const pos = shuffleOrder.indexOf(index)
    if (pos >= 0) shufflePos = pos
  }
  syncMediaSessionNow({ position: true })

  const startedAt = nowMs()
  const nextUrl = await resolvePlaybackUrl(track.file)
  if (seq !== applyTrackSeq || currentIndex.value !== index) return
  logSlowPlayback('resolve-url', startedAt, track, {
    embedded: usesEmbeddedServer(),
  })
  track.url = nextUrl

  const sameSource =
    playingFile === track.file &&
    (isSameAudioFile(a.src, track.file) || isSameAudioUrl(a.src, nextUrl))

  try {
    if (!sameSource) {
      beginTrackChange()
      a.pause()
      if (seq !== applyTrackSeq) return
      isPlaying.value = false
      stopProgressTicker()
      playingFile = track.file
      httpFallbackTriedFor = ''
      a.src = nextUrl
      const reportLoadedMetadata = () => {
        if (seq === applyTrackSeq && playingFile === track.file) {
          logSlowPlayback('loaded-metadata', startedAt, track)
        }
      }
      const reportPlaying = () => {
        if (seq === applyTrackSeq && playingFile === track.file) {
          logSlowPlayback('playing', startedAt, track)
        }
      }
      a.addEventListener('loadedmetadata', reportLoadedMetadata, { once: true })
      a.addEventListener('playing', reportPlaying, { once: true })
      a.load()
      if (resetTime) {
        currentTime.value = 0
        duration.value = 0
        if (!(restoreTime > 0)) {
          a.addEventListener(
            'loadedmetadata',
            () => {
              if (seq !== applyTrackSeq || playingFile !== track.file) return
              try {
                a.currentTime = 0
              } catch {
                // Seeking before the resource is seekable can abort the load.
              }
              currentTime.value = 0
            },
            { once: true }
          )
        }
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
        setPlaybackIntent(true)
        await playAudioWithRecovery(a)
      }
      preloadPlaybackUrlAt(index + 1)
      if (shuffle.value && shuffleOrder.length) {
        preloadPlaybackUrlAt(shuffleOrder[shufflePos + 1])
      }
      return
    }

    if ((autoplay || wasPlaying) && a.paused) {
      setPlaybackIntent(true)
      await playAudioWithRecovery(a)
    }
    preloadPlaybackUrlAt(index + 1)
    if (shuffle.value && shuffleOrder.length) {
      preloadPlaybackUrlAt(shuffleOrder[shufflePos + 1])
    }
  } finally {
    if (seq === applyTrackSeq && !(autoplay || wasPlaying)) {
      endTrackChange()
    }
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
    const wasPlaying = isPlaying.value || playbackIntent.value
    const metaByFile = libraryMetaByFile()
    playlist.value = paths.map((file) => trackFromFile(file, metaByFile))
    currentIndex.value = paths.indexOf(currentFile)
    if (shuffle.value) buildShuffleOrder()

    const track = playlist.value[currentIndex.value]
    const a = ensureAudio()
    if (track && !isSameAudioFile(a.src, track.file)) {
      selectAt(currentIndex.value)
      return
    }
    if (wasPlaying && a.paused) {
      setPlaybackIntent(true)
      playAudioWithRecovery(a)
    }
    return
  }

  if (currentFile && !paths.includes(currentFile)) {
    return
  }

  setPlaylist(paths, options)
}

function followOnAlbum(context) {
  if (context?.type !== 'album' || !context.artist || !context.name) return null
  const albums = groupAlbums(getCachedLibraryItems() || [])
  return nextAlbumAfter(albums, context.artist, context.name)
}

function setPlaylist(files, options = {}) {
  const metaByFile = libraryMetaByFile()
  let tracks = (files || []).map((f) =>
    typeof f === 'string' ? trackFromFile(f, metaByFile) : f
  )
  let context = options.context || null
  if (context?.type === 'album' && !shuffle.value) {
    const nextAlbum = followOnAlbum(context)
    if (nextAlbum?.files?.length) {
      const currentFiles = tracks.map((track) => track.file)
      const packed = filesWithFollowOnAlbum(currentFiles, nextAlbum)
      tracks = packed.files.map((file) =>
        tracks.find((track) => track.file === file) ||
          trackFromFile(file, metaByFile)
      )
      context = {
        ...context,
        followOnStart: packed.followOnStart,
        followOnName: nextAlbum.name,
      }
    }
  }
  playlist.value = tracks
  if (Object.prototype.hasOwnProperty.call(options, 'context')) {
    playlistContext.value = context
  } else if (!playlistContext.value) {
    playlistContext.value = context
  }
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
  setPlaybackIntent(true)
  playAudioWithRecovery(a)
}

function pause() {
  setPlaybackIntent(false)
  endTrackChange()
  resetRecovery()
  clearPlaybackStartWatchdog()
  if (audio) audio.pause()
  persistPlayerSession(true)
}

function toggle() {
  if (playbackIntent.value || isPlaying.value) pause()
  else play()
}

function seek(seconds) {
  const a = ensureAudio()
  const max =
    Number.isFinite(duration.value) && duration.value > 0
      ? duration.value
      : Number.isFinite(a.duration) && a.duration > 0
        ? a.duration
        : 0
  const clamped = clampedSeekSeconds(seconds, max)
  if (clamped == null) {
    clearSeekLock()
    return
  }
  currentTime.value = clamped
  lastMediaPositionSyncAt = 0
  if (!seekWouldMove(a.currentTime, clamped)) {
    clearSeekLock()
    syncMediaSessionNow({ position: true })
    return
  }
  isSeeking = true
  if (seekClearTimer) clearTimeout(seekClearTimer)
  seekClearTimer = setTimeout(() => {
    seekClearTimer = 0
    isSeeking = false
  }, 750)
  try {
    a.currentTime = clamped
  } catch {
    clearSeekLock()
  }
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
  if (shuffle.value && shuffleOrder.length !== playlist.value.length) {
    buildShuffleOrder()
  }
  return nextIndexInOrder({
    length: playlist.value.length,
    currentIndex: currentIndex.value,
    shuffle: shuffle.value,
    shuffleOrder,
    shufflePos,
    repeatMode: repeatMode.value,
  })
}

function prevIndex() {
  if (shuffle.value && shuffleOrder.length !== playlist.value.length) {
    buildShuffleOrder()
  }
  return prevIndexInOrder({
    length: playlist.value.length,
    currentIndex: currentIndex.value,
    shuffle: shuffle.value,
    shuffleOrder,
    shufflePos,
    repeatMode: repeatMode.value,
  })
}

function tryContinueArtistDiscography() {
  if (shuffle.value || repeatMode.value === 'all') return false
  const ctx = playlistContext.value
  if (ctx?.type !== 'album') return false
  const nextAlbum = followOnAlbum(ctx)
  if (!nextAlbum?.files?.length) return false
  const start = playlist.value.length
  const extra = nextAlbum.files
    .filter((file) => !playlist.value.some((track) => track.file === file))
    .map((file) => trackFromFile(file, libraryMetaByFile()))
  if (!extra.length) return false
  playlist.value = [...playlist.value, ...extra]
  playlistContext.value = {
    type: 'album',
    name: nextAlbum.name,
    artist: ctx.artist,
    continuedFrom: ctx.name,
  }
  playAt(start)
  return true
}

function next() {
  const i = nextIndex()
  if (i < 0) {
    if (tryContinueArtistDiscography()) return
    pause()
    return
  }
  const followOnStart = Number(playlistContext.value?.followOnStart)
  if (
    Number.isFinite(followOnStart) &&
    followOnStart >= 0 &&
    i >= followOnStart &&
    playlistContext.value?.followOnName
  ) {
    playlistContext.value = {
      type: 'album',
      name: playlistContext.value.followOnName,
      artist: playlistContext.value.artist,
      continuedFrom: playlistContext.value.name,
    }
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
      setPlaybackIntent(true)
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
    playbackIntent,
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
