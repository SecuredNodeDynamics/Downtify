<template>
  <div class="min-h-screen">
    <Navbar />

    <div class="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <!-- Loading -->
      <div v-if="loading" class="space-y-3">
        <div class="skeleton h-32 rounded-2xl" />
        <div v-for="n in 4" :key="n" class="skeleton h-20 rounded-2xl" />
      </div>

      <!-- Error -->
      <div
        v-else-if="error"
        class="surface rounded-2xl p-8 flex flex-col items-center text-center gap-3"
      >
        <Icon
          icon="clarity:exclamation-circle-line"
          class="h-10 w-10 text-error"
        />
        <p class="text-sm text-error">{{ error }}</p>
        <button class="btn btn-sm btn-ghost mt-2" @click="router.back()">
          Go back
        </button>
      </div>

      <template v-else-if="tracks.length">
        <!-- Album / Playlist header -->
        <div
          v-if="type !== 'track'"
          class="surface rounded-2xl p-5 mb-6 flex gap-5 items-center"
        >
          <img
            v-if="tracks[0]?.cover_url"
            :src="coverSrc(tracks[0]?.cover_url)"
            class="h-20 w-20 rounded-xl object-cover shrink-0 shadow-lg"
          />
          <div class="flex-1 min-w-0">
            <p
              class="text-xs text-base-content/40 uppercase tracking-widest mb-1"
            >
              {{ type === 'album' ? 'Album' : 'Playlist' }}
            </p>
            <h1 class="text-xl font-bold truncate">
              {{ tracks[0]?.album_name || 'Unknown' }}
            </h1>
            <p class="text-sm text-base-content/60 truncate mt-0.5">
              {{ tracks[0]?.artist }}
              <span v-if="tracks[0]?.year" class="text-base-content/30">
                · {{ tracks[0].year }}</span
              >
            </p>
            <p class="text-xs text-base-content/40 mt-1">
              {{ tracks.length }} tracks
            </p>
          </div>
          <!-- Download all -->
          <button
            class="btn btn-primary btn-sm gap-2 shrink-0"
            :disabled="allQueued"
            @click="downloadAll"
          >
            <Icon icon="clarity:download-line" class="h-4 w-4" />
            {{ allQueued ? 'Queued' : 'Download All' }}
          </button>
        </div>

        <!-- Track list -->
        <ul class="space-y-2">
          <li
            v-for="(song, index) in tracks"
            :key="song.song_id || index"
            class="surface rounded-2xl flex items-center gap-3 p-3 transition-all"
            :class="{
              'ring-1 ring-primary/30':
                currentTrack?.song_id === song.song_id && isPlaying,
            }"
          >
            <!-- Cover (single track view shows larger) -->
            <div
              class="relative shrink-0 rounded-xl overflow-hidden bg-base-content/10"
              :class="type === 'track' ? 'h-20 w-20' : 'h-14 w-14'"
            >
              <img
                v-if="song.cover_url"
                :src="coverSrc(song.cover_url)"
                :alt="song.name"
                class="h-full w-full object-cover"
                loading="lazy"
              />
              <div
                v-else
                class="h-full w-full flex items-center justify-center text-base-content/30"
              >
                <Icon icon="clarity:music-note-line" class="h-6 w-6" />
              </div>

              <!-- Play overlay -->
              <button
                v-if="song.preview_url || embedUrlFor(song)"
                class="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 hover:opacity-100 transition-opacity"
                :class="{
                  'opacity-100': currentTrack?.song_id === song.song_id,
                }"
                @click="togglePlay(song)"
              >
                <Icon
                  :icon="
                    currentTrack?.song_id === song.song_id && isPlaying
                      ? 'clarity:pause-solid'
                      : 'clarity:play-solid'
                  "
                  class="h-6 w-6 text-white drop-shadow"
                />
              </button>
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-0.5">
                <span class="font-semibold truncate text-sm">{{
                  song.name
                }}</span>
                <span
                  v-if="song.explicit"
                  class="badge-error-soft shrink-0 text-xs"
                  >E</span
                >
              </div>
              <p class="text-xs text-base-content/60 truncate">
                {{ artistsOf(song) }}
              </p>
              <p
                v-if="type !== 'track' && song.album_name"
                class="text-xs text-base-content/40 truncate"
              >
                {{ song.album_name }}
              </p>
              <!-- No preview notice -->
              <p
                v-if="!song.preview_url && !embedUrlFor(song)"
                class="text-xs text-base-content/30 mt-0.5 italic"
              >
                No playable preview available
              </p>
            </div>

            <!-- Duration -->
            <span class="text-xs text-base-content/40 shrink-0 tabular-nums">
              {{ formatDuration(song.duration) }}
            </span>

            <!-- Actions -->
            <div class="flex items-center gap-1 shrink-0">
              <a
                v-if="song.url"
                class="icon-btn"
                :href="song.url"
                target="_blank"
                rel="noopener"
                title="Open on Spotify"
              >
                <Icon icon="clarity:pop-out-line" class="h-4 w-4" />
              </a>
              <button
                v-if="downloadState(song) === 'queued'"
                class="icon-btn text-primary cursor-default"
                title="In queue"
                disabled
              >
                <Icon icon="clarity:check-circle-line" class="h-5 w-5" />
              </button>
              <button
                v-else
                class="icon-btn text-primary hover:bg-primary/10"
                @click="downloadOne(song)"
                title="Download"
              >
                <Icon icon="clarity:download-line" class="h-5 w-5" />
              </button>
            </div>
          </li>
        </ul>
      </template>
    </div>

    <!-- Mini player bar -->
    <Transition name="player-bar">
      <div
        v-if="currentTrack"
        class="fixed bottom-0 left-0 right-0 z-50 surface border-t border-base-content/10 px-4 py-3 flex items-center gap-4 shadow-2xl"
      >
        <!-- Cover -->
        <img
          v-if="currentTrack.cover_url"
          :src="coverSrc(currentTrack.cover_url)"
          class="h-10 w-10 rounded-lg object-cover shrink-0"
        />

        <!-- Info -->
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold truncate">{{ currentTrack.name }}</p>
          <p class="text-xs text-base-content/60 truncate">
            {{ artistsOf(currentTrack) }}
          </p>
        </div>

        <!-- Progress -->
        <div
          v-if="currentTrack.preview_url"
          class="hidden sm:flex flex-1 items-center gap-2 max-w-sm"
        >
          <span
            class="text-xs text-base-content/40 tabular-nums w-8 text-right"
            >{{ formatDuration(Math.floor(audioProgress)) }}</span
          >
          <input
            type="range"
            min="0"
            :max="audioDuration || 30"
            :value="audioProgress"
            class="flex-1 h-1 accent-primary cursor-pointer"
            @input="seek($event.target.value)"
          />
          <span class="text-xs text-base-content/40 tabular-nums w-8">{{
            formatDuration(Math.floor(audioDuration))
          }}</span>
        </div>
        <div
          v-else-if="currentEmbedUrl"
          class="hidden sm:block flex-1 max-w-md overflow-hidden rounded-xl border border-white/10 bg-black/20"
        >
          <iframe
            :key="currentEmbedUrl"
            :src="currentEmbedUrl"
            class="h-20 w-full"
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            loading="lazy"
          />
        </div>

        <!-- Controls -->
        <div class="flex items-center gap-2 shrink-0">
          <button class="icon-btn" @click="togglePlay(currentTrack)">
            <Icon
              :icon="isPlaying ? 'clarity:pause-solid' : 'clarity:play-solid'"
              class="h-5 w-5"
            />
          </button>
          <button class="icon-btn" @click="stopPlayback" title="Close player">
            <Icon icon="clarity:times-line" class="h-4 w-4" />
          </button>
        </div>

        <!-- Download from player bar -->
        <button
          class="btn btn-primary btn-sm gap-1.5 shrink-0"
          :disabled="downloadState(currentTrack) === 'queued'"
          @click="downloadOne(currentTrack)"
        >
          <Icon icon="clarity:download-line" class="h-4 w-4" />
          {{ downloadState(currentTrack) === 'queued' ? 'Queued' : 'Download' }}
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'

import Navbar from '/src/components/Navbar.vue'
import { useDownloadManager } from '../model/download'
import { useProgressTracker } from '../model/download'
import API from '../model/api'

const route = useRoute()
const router = useRouter()
const dm = useDownloadManager()
const pt = useProgressTracker()

function coverSrc(url) {
  return API.mediaUrl(url)
}

// ── State ────────────────────────────────────────────────────────────────────
const loading = ref(true)
const error = ref(null)
const tracks = ref([])
const type = ref('track')

// ── Audio ────────────────────────────────────────────────────────────────────
const audio = new Audio()
const currentTrack = ref(null)
const isPlaying = ref(false)
const audioProgress = ref(0)
const audioDuration = ref(30)
const currentEmbedUrl = computed(() => embedUrlFor(currentTrack.value))

audio.addEventListener('timeupdate', () => {
  audioProgress.value = audio.currentTime
})
audio.addEventListener('durationchange', () => {
  audioDuration.value = audio.duration || 30
})
audio.addEventListener('ended', () => {
  isPlaying.value = false
  audioProgress.value = 0
})

onBeforeUnmount(() => {
  audio.pause()
  audio.src = ''
})

// ── Load preview data ────────────────────────────────────────────────────────
onMounted(async () => {
  const url = route.query.url
  if (!url) {
    error.value = 'No URL provided.'
    loading.value = false
    return
  }
  try {
    const res = await API.preview(url)
    type.value = res.data.type
    tracks.value = res.data.tracks || []
  } catch (err) {
    error.value =
      err?.response?.data?.detail || err.message || 'Failed to load preview.'
  } finally {
    loading.value = false
  }
})

// ── Playback ─────────────────────────────────────────────────────────────────
function togglePlay(song) {
  if (!song.preview_url) {
    if (embedUrlFor(song)) {
      audio.pause()
      currentTrack.value = song
      isPlaying.value = false
    }
    return
  }

  if (currentTrack.value?.song_id === song.song_id) {
    // Same track — toggle pause/play
    if (isPlaying.value) {
      audio.pause()
      isPlaying.value = false
    } else {
      audio.play()
      isPlaying.value = true
    }
  } else {
    // New track
    audio.pause()
    audio.src = song.preview_url
    audio.currentTime = 0
    audioProgress.value = 0
    currentTrack.value = song
    audio.play()
    isPlaying.value = true
  }
}

function stopPlayback() {
  audio.pause()
  audio.src = ''
  currentTrack.value = null
  isPlaying.value = false
  audioProgress.value = 0
}

function seek(value) {
  audio.currentTime = Number(value)
  audioProgress.value = Number(value)
}

// ── Download ─────────────────────────────────────────────────────────────────
function downloadOne(song) {
  dm.queue(song)
  router.push({ name: 'Download' })
}

const allQueued = ref(false)
function downloadAll() {
  tracks.value.forEach((song) => dm.queue(song))
  allQueued.value = true
  router.push({ name: 'Download' })
}

function downloadState(song) {
  const item = pt.getBySong(song)
  if (!item) return 'idle'
  if (item.isErrored()) return 'error'
  if (item.isDownloaded()) return 'queued'
  return 'queued'
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function artistsOf(song) {
  if (Array.isArray(song.artists) && song.artists.length)
    return song.artists.join(', ')
  return song.artist || 'Unknown Artist'
}

function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function embedUrlFor(song) {
  if (!song?.url) return ''
  const spotifyMatch = song.url.match(
    /open\.spotify\.com\/(?:intl-[a-z]{2}\/)?(track|album|playlist)\/([A-Za-z0-9]+)/
  )
  if (spotifyMatch) {
    return `https://open.spotify.com/embed/${spotifyMatch[1]}/${spotifyMatch[2]}`
  }

  const youtubeId =
    song.song_id ||
    song.url.match(/[?&]v=([A-Za-z0-9_-]{6,})/)?.[1] ||
    song.url.match(/youtu\.be\/([A-Za-z0-9_-]{6,})/)?.[1]
  if (
    song.source === 'youtube' &&
    youtubeId &&
    !String(youtubeId).startsWith('album:')
  ) {
    return `https://www.youtube.com/embed/${youtubeId}`
  }
  return ''
}
</script>

<style scoped>
.player-bar-enter-active,
.player-bar-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.player-bar-enter-from,
.player-bar-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
