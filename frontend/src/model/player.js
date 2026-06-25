import { ref, computed } from 'vue'

import API from './api.js'
import {
  isSameAudioFile,
  isSameAudioUrl,
  resolvePlaybackUrl,
} from './playerAudioUrl.js'
import { usesEmbeddedServer } from './serverConnection.js'

const VOLUME_KEY = 'downtify-player-volume'

const playlist = ref([])
const currentIndex = ref(-1)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(parseFloat(localStorage.getItem(VOLUME_KEY) || '0.85'))
const isMuted = ref(false)
const repeatMode = ref('off') // 'off' | 'all' | 'one'
const shuffle = ref(false)

let audio = null
let shuffleOrder = []
let shufflePos = 0
let progressRaf = 0
let isSeeking = false
let playingFile = ''

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
  })
  audio.addEventListener('play', () => {
    isPlaying.value = true
    startProgressTicker()
  })
  audio.addEventListener('pause', () => {
    isPlaying.value = false
    stopProgressTicker()
    if (audio) currentTime.value = audio.currentTime
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

async function applyTrack(index, { autoplay = false, resetTime = true } = {}) {
  if (index < 0 || index >= playlist.value.length) return
  const a = ensureAudio()
  const wasPlaying = isPlaying.value
  const track = playlist.value[index]
  currentIndex.value = index
  if (shuffle.value) {
    if (shuffleOrder.length !== playlist.value.length) buildShuffleOrder()
    const pos = shuffleOrder.indexOf(index)
    if (pos >= 0) shufflePos = pos
  }

  const nextUrl = await resolvePlaybackUrl(track.file)
  track.url = nextUrl

  const sameSource =
    playingFile === track.file &&
    (isSameAudioFile(a.src, track.file) || isSameAudioUrl(a.src, nextUrl))

  if (!sameSource) {
    a.pause()
    isPlaying.value = false
    stopProgressTicker()
    playingFile = track.file
    a.src = nextUrl
    if (resetTime) {
      a.currentTime = 0
      currentTime.value = 0
      duration.value = 0
    }
    if (autoplay || wasPlaying) {
      await a.play().catch(() => {})
    }
    return
  }

  if ((autoplay || wasPlaying) && a.paused) {
    await a.play().catch(() => {})
  }
}

export function syncPlaylistFromFiles(files, options = {}) {
  const paths = (files || []).filter(Boolean)
  if (!paths.length) return

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
      a.play().catch(() => {})
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
  a.play().catch(() => {})
}

function pause() {
  if (audio) audio.pause()
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
    if (audio) audio.play().catch(() => {})
    return
  }
  next()
}

function setRepeat(mode) {
  if (['off', 'all', 'one'].includes(mode)) repeatMode.value = mode
}

function cycleRepeat() {
  const order = ['off', 'all', 'one']
  const i = order.indexOf(repeatMode.value)
  setRepeat(order[(i + 1) % order.length])
}

function setShuffle(v) {
  shuffle.value = !!v
  if (shuffle.value) buildShuffleOrder()
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
    currentIndex,
    currentTrack,
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
