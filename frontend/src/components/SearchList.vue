<template>
  <div class="mx-auto max-w-4xl px-4 py-8 sm:px-6">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold tracking-tight">{{ t('search.title') }}</h1>
      <p class="mt-1 text-sm text-base-content/60">
        <template v-if="sm.searchTerm.value">
          {{ t('search.matchesFor') }}
          <span class="text-base-content/90 font-medium">
            "{{ sm.searchTerm.value }}"
          </span>
          <template
            v-if="!sm.isSearching.value && (props.data?.length || 0) > 0"
          >
            {{
              props.data.length === 1
                ? t('search.resultsCount', { count: props.data.length })
                : t('search.resultsCountPlural', { count: props.data.length })
            }}
          </template>
        </template>
        <template v-else>{{ t('search.typeToBegin') }}</template>
      </p>
    </div>

    <!-- Error -->
    <div
      v-if="props.error"
      class="surface rounded-2xl p-4 mb-4 flex gap-3 items-center text-sm text-error"
    >
      <Icon icon="clarity:exclamation-circle-line" class="h-5 w-5 shrink-0" />
      <span>
        {{
          sm.errorValue.value
            ? t('search.errorWithDetail', { detail: sm.errorValue.value })
            : t('search.error')
        }}
      </span>
    </div>

    <!-- Loading skeleton -->
    <div v-if="sm.isSearching.value" class="space-y-3">
      <div v-for="n in 5" :key="n" class="skeleton h-24 rounded-2xl" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!props.data || props.data.length === 0"
      class="surface rounded-2xl p-12 flex flex-col items-center text-center"
    >
      <Icon
        icon="clarity:search-line"
        class="h-12 w-12 text-base-content/20 mb-4"
      />
      <p class="text-base-content/50 text-sm">{{ t('search.empty') }}</p>
      <p class="text-base-content/40 text-xs mt-1">
        {{ t('search.emptyHint') }}
      </p>
    </div>

    <!-- Results -->
    <ul v-else class="space-y-2">
      <li
        v-for="(song, index) in paginatedData"
        :key="song.song_id || index"
        class="surface rounded-2xl track-card"
      >
        <!-- Cover -->
        <div class="track-cover">
          <img
            v-if="song.cover_url"
            :src="song.cover_url"
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
        </div>

        <!-- Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-0.5">
            <span class="font-semibold truncate">{{ song.name }}</span>
            <span v-if="song.explicit" class="badge-error-soft shrink-0"
              >E</span
            >
          </div>
          <p class="text-xs text-base-content/70 truncate">
            {{ artistsOf(song) }}
          </p>
          <p
            v-if="song.album_name"
            class="text-xs text-base-content/40 truncate"
          >
            {{ song.album_name }}
            <span v-if="song.year" class="text-base-content/30">
              · {{ song.year }}
            </span>
          </p>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-1 shrink-0">
          <span
            class="media-type-pill"
            :class="mediaTypeClass(song)"
            :title="mediaTypeLabel(song)"
          >
            {{ mediaTypeLabel(song) }}
          </span>

          <button
            class="icon-btn text-primary hover:bg-primary/10"
            @click="openDemo(song)"
            :title="t('search.demo')"
          >
            <Icon icon="clarity:play-solid" class="h-4 w-4" />
          </button>

          <a
            v-if="song.url"
            class="icon-btn"
            :href="song.url"
            target="_blank"
            rel="noopener"
            :title="t('search.openOnSpotify')"
          >
            <Icon icon="clarity:pop-out-line" class="h-4 w-4" />
          </a>

          <button
            v-if="downloadState(song) === 'queued'"
            class="icon-btn text-primary cursor-default"
            :title="t('search.inQueue')"
            disabled
          >
            <Icon icon="clarity:check-circle-line" class="h-5 w-5" />
          </button>
          <button
            v-else
            class="icon-btn text-primary hover:bg-primary/10"
            @click="download(song)"
            :title="t('search.download')"
          >
            <Icon icon="clarity:download-line" class="h-5 w-5" />
          </button>
        </div>
      </li>
    </ul>

    <!-- Pagination -->
    <nav
      v-if="totalPages > 1"
      class="mt-8 flex items-center justify-center gap-1 flex-wrap"
    >
      <button
        class="icon-btn"
        :disabled="currentPage === 1"
        @click="currentPage--"
        :title="t('search.previousPage')"
      >
        <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-[-90deg]" />
      </button>
      <button
        v-for="page in totalPages"
        :key="page"
        class="h-10 min-w-[2.5rem] rounded-full px-3 text-sm font-medium transition-colors"
        :class="
          page === currentPage
            ? 'bg-primary text-primary-content shadow-glow-sm'
            : 'text-base-content/70 hover:text-base-content hover:bg-white/10'
        "
        @click="currentPage = page"
      >
        {{ page }}
      </button>
      <button
        class="icon-btn"
        :disabled="currentPage === totalPages"
        @click="currentPage++"
        :title="t('search.nextPage')"
      >
        <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-90" />
      </button>
    </nav>

    <!-- Demo modal -->
    <Teleport to="body">
      <Transition name="demo-modal">
        <div
          v-if="demoOpen"
          class="fixed inset-0 z-[80] flex items-end justify-center bg-black/60 p-0 backdrop-blur-sm sm:items-center sm:p-6"
          @click.self="closeDemo"
        >
          <div
            class="surface-strong w-full max-w-2xl overflow-hidden rounded-t-3xl shadow-2xl sm:rounded-3xl"
          >
            <div class="flex items-center justify-between border-b border-white/5 px-5 py-4">
              <div class="min-w-0">
                <p class="text-xs font-semibold uppercase tracking-wider text-base-content/50">
                  {{ demoTypeLabel }}
                </p>
                <h2 class="truncate text-lg font-bold tracking-tight">
                  {{ demoTitle }}
                </h2>
              </div>
              <button class="icon-btn shrink-0" @click="closeDemo" :title="t('common.close')">
                <Icon icon="clarity:close-line" class="h-5 w-5" />
              </button>
            </div>

            <div v-if="demoLoading" class="space-y-3 p-5">
              <div class="skeleton h-36 rounded-2xl" />
              <div class="skeleton h-14 rounded-2xl" />
              <div class="skeleton h-14 rounded-2xl" />
            </div>

            <div
              v-else-if="demoError"
              class="flex flex-col items-center gap-3 p-8 text-center text-sm text-error"
            >
              <Icon icon="clarity:exclamation-circle-line" class="h-10 w-10" />
              <p>{{ demoError }}</p>
            </div>

            <template v-else>
              <div class="grid gap-5 p-5 sm:grid-cols-[160px_1fr]">
                <div class="relative aspect-square overflow-hidden rounded-2xl bg-base-content/10 shadow-lg">
                  <img
                    v-if="activeDemoTrack?.cover_url"
                    :src="activeDemoTrack.cover_url"
                    :alt="activeDemoTrack.name"
                    class="h-full w-full object-cover"
                  />
                  <div
                    v-else
                    class="flex h-full w-full items-center justify-center text-base-content/30"
                  >
                    <Icon icon="clarity:music-note-line" class="h-12 w-12" />
                  </div>
                  <button
                    class="absolute inset-0 flex items-center justify-center bg-black/35 transition hover:bg-black/45 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="demoAudioResolving"
                    @click="toggleDemoPlay(activeDemoTrack)"
                    :title="playButtonTitle"
                  >
                    <Icon
                      :icon="demoAudioResolving ? 'clarity:refresh-line' : (demoPlaying ? 'clarity:pause-solid' : 'clarity:play-solid')"
                      class="h-12 w-12 text-white drop-shadow"
                    />
                  </button>
                </div>

                <div class="min-w-0">
                  <h3 class="truncate text-xl font-bold">{{ activeDemoTrack?.name }}</h3>
                  <p class="truncate text-sm text-base-content/60">
                    {{ activeDemoTrack ? artistsOf(activeDemoTrack) : '' }}
                  </p>
                  <p
                    v-if="activeDemoTrack?.album_name"
                    class="mt-1 truncate text-xs text-base-content/40"
                  >
                    {{ activeDemoTrack.album_name }}
                    <span v-if="activeDemoTrack.year"> · {{ activeDemoTrack.year }}</span>
                  </p>

                  <div class="mt-5 flex items-center gap-2">
                    <span class="w-9 text-right text-xs tabular-nums text-base-content/40">
                      {{ formatDuration(Math.floor(demoProgress)) }}
                    </span>
                    <input
                      type="range"
                      min="0"
                      :max="demoDuration || 30"
                      :value="demoProgress"
                      class="h-1 flex-1 cursor-pointer accent-primary"
                      :disabled="!activeDemoAudioUrl"
                      @input="seekDemo($event.target.value)"
                    />
                    <span class="w-9 text-xs tabular-nums text-base-content/40">
                      {{ formatDuration(Math.floor(demoDuration)) }}
                    </span>
                  </div>

                  <div
                    v-if="demoVolumeActive"
                    class="mt-3 flex items-center gap-2 text-base-content/50"
                  >
                    <Icon :icon="demoVolumeIcon" class="h-4 w-4 shrink-0" />
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      :value="demoVolume"
                      class="h-1 w-32 cursor-pointer accent-primary sm:w-40"
                      aria-label="Volume"
                      @input="setDemoVolume($event.target.value)"
                    />
                    <span class="w-9 text-xs tabular-nums">
                      {{ Math.round(demoVolume * 100) }}%
                    </span>
                  </div>

                  <p
                    v-if="demoAudioResolving"
                    class="mt-3 text-xs italic text-base-content/40"
                  >
                    Preparing preview...
                  </p>

                  <p
                    v-else-if="demoAudioError"
                    class="mt-3 text-xs italic text-error"
                  >
                    {{ demoAudioError }}
                  </p>

                  <p
                    v-else-if="!activeDemoTrack?.preview_url && !activeDemoAudioUrl"
                    class="mt-3 text-xs italic text-base-content/40"
                  >
                    Press play to listen in this popup.
                  </p>

                  <div class="mt-5 flex flex-wrap items-center gap-2">
                    <button
                      v-if="demoType === 'album' && demoSourceItem"
                      class="btn btn-primary btn-sm gap-2 rounded-full"
                      :disabled="downloadState(demoSourceItem) === 'queued'"
                      @click="downloadAlbumFromDemo"
                    >
                      <Icon icon="clarity:download-line" class="h-4 w-4" />
                      {{
                        downloadState(demoSourceItem) === 'queued'
                          ? t('search.inQueue')
                          : t('search.downloadAlbum')
                      }}
                    </button>
                    <button
                      class="btn btn-primary btn-sm gap-2 rounded-full"
                      :disabled="downloadState(activeDemoTrack) === 'queued'"
                      @click="downloadFromDemo"
                    >
                      <Icon icon="clarity:download-line" class="h-4 w-4" />
                      {{
                        downloadState(activeDemoTrack) === 'queued'
                          ? t('search.inQueue')
                          : t('search.download')
                      }}
                    </button>
                    <a
                      v-if="activeDemoTrack?.url"
                      class="btn btn-sm gap-2 rounded-full border-white/10 bg-base-100/85"
                      :href="activeDemoTrack.url"
                      target="_blank"
                      rel="noopener"
                    >
                      <Icon icon="clarity:pop-out-line" class="h-4 w-4" />
                      {{ t('search.openOnSpotify') }}
                    </a>
                  </div>
                </div>
              </div>

              <div
                v-if="demoType === 'album' && demoTracks.length"
                class="max-h-64 overflow-y-auto border-t border-white/5 p-3"
              >
                <div
                  v-for="(track, index) in demoTracks"
                  :key="track.song_id || index"
                  class="flex w-full cursor-pointer items-center gap-3 rounded-xl px-2 py-2 text-left transition-colors hover:bg-white/5"
                  :class="{ 'bg-primary/10 text-primary': activeDemoTrack?.song_id === track.song_id }"
                  @click="selectDemoTrack(track)"
                  role="button"
                  tabindex="0"
                  @keydown.enter.prevent="selectDemoTrack(track)"
                  @keydown.space.prevent="selectDemoTrack(track)"
                >
                  <img
                    v-if="track.cover_url"
                    :src="track.cover_url"
                    :alt="track.name"
                    class="h-10 w-10 shrink-0 rounded-lg object-cover"
                  />
                  <div
                    v-else
                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-base-content/10"
                  >
                    <Icon icon="clarity:music-note-line" class="h-4 w-4" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-medium">{{ track.name }}</p>
                    <p class="truncate text-xs text-base-content/50">
                      {{ artistsOf(track) }}
                    </p>
                  </div>
                  <button
                    class="icon-btn shrink-0"
                    :disabled="demoAudioResolving && activeDemoTrack?.song_id === track.song_id"
                    @click.stop="toggleDemoPlay(track)"
                    :title="playButtonTitle"
                  >
                    <Icon
                      :icon="activeDemoTrack?.song_id === track.song_id && demoAudioResolving
                        ? 'clarity:refresh-line'
                        : activeDemoTrack?.song_id === track.song_id && demoPlaying
                        ? 'clarity:pause-solid'
                        : 'clarity:play-solid'"
                      class="h-4 w-4"
                    />
                  </button>
                </div>
              </div>
            </template>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { Icon } from '@iconify/vue'

import { useSearchManager } from '../model/search'
import { useProgressTracker, useDownloadManager } from '../model/download'
import { useI18n } from '../i18n'
import API from '../model/api'

const PAGE_SIZE = 5

const props = defineProps(['data', 'error'])
const emit = defineEmits(['download'])

const sm = useSearchManager()
const pt = useProgressTracker()
const dm = useDownloadManager()
const { t } = useI18n()

const currentPage = ref(1)
const demoOpen = ref(false)
const demoLoading = ref(false)
const demoError = ref('')
const demoTracks = ref([])
const demoType = ref('track')
const demoSourceItem = ref(null)
const activeDemoTrack = ref(null)
const demoProgress = ref(0)
const demoDuration = ref(30)
const demoPlaying = ref(false)
const demoAudioResolving = ref(false)
const demoAudioError = ref('')
const demoVolume = ref(1)
const demoVolumeActive = ref(false)
const resolvedDemoAudioUrls = ref({})
const resolvingDemoAudioKeys = ref({})
const demoAudio = new Audio()
demoAudio.volume = demoVolume.value

demoAudio.addEventListener('timeupdate', () => {
  demoProgress.value = demoAudio.currentTime
})
demoAudio.addEventListener('durationchange', () => {
  demoDuration.value = demoAudio.duration || 30
})
demoAudio.addEventListener('ended', () => {
  demoPlaying.value = false
  demoProgress.value = 0
})

onBeforeUnmount(() => {
  stopDemoPlayback()
})

const totalPages = computed(() =>
  Math.ceil((props.data?.length || 0) / PAGE_SIZE)
)

const paginatedData = computed(() => {
  if (!props.data) return []
  const start = (currentPage.value - 1) * PAGE_SIZE
  return props.data.slice(start, start + PAGE_SIZE)
})

const demoTypeLabel = computed(() =>
  demoType.value === 'album' ? t('search.albumType') : t('search.trackType')
)

const demoTitle = computed(() => {
  const first = demoTracks.value[0]
  if (demoType.value === 'album') return first?.album_name || first?.name || ''
  return first?.name || ''
})

const activeDemoAudioUrl = computed(
  () =>
    activeDemoTrack.value?.preview_url ||
    resolvedDemoAudioUrls.value[demoTrackKey(activeDemoTrack.value)] ||
    ''
)

const playButtonTitle = computed(() =>
  demoPlaying.value ? t('player.pause') : t('player.play')
)

const demoVolumeIcon = computed(() => {
  if (demoVolume.value <= 0) return 'clarity:volume-mute-line'
  if (demoVolume.value < 0.5) return 'clarity:volume-down-line'
  return 'clarity:volume-up-line'
})

watch(
  () => props.data,
  () => {
    currentPage.value = 1
  }
)

function artistsOf(song) {
  if (Array.isArray(song.artists) && song.artists.length) {
    return song.artists.join(', ')
  }
  return song.artist || t('common.unknownArtist')
}

function mediaType(song) {
  return song?.media_type === 'album' ? 'album' : 'track'
}

function mediaTypeLabel(song) {
  return mediaType(song) === 'album'
    ? t('search.albumType')
    : t('search.trackType')
}

function mediaTypeClass(song) {
  return mediaType(song) === 'album'
    ? 'media-type-pill-album'
    : 'media-type-pill-track'
}

function downloadState(song) {
  if (!song) return 'idle'
  const item = pt.getBySong(song)
  if (!item) return 'idle'
  if (item.isErrored()) return 'error'
  if (item.isDownloaded()) return 'queued'
  return 'queued'
}

function download(song) {
  emit('download', song)
}

async function openDemo(song) {
  demoOpen.value = true
  demoLoading.value = true
  demoError.value = ''
  demoTracks.value = []
  demoSourceItem.value = song
  activeDemoTrack.value = null
  demoAudioError.value = ''
  demoVolumeActive.value = false
  stopDemoPlayback()

  try {
    if (song?.media_type === 'album' && song.browse_id) {
      const res = await API.openYoutubeAlbum(song.browse_id)
      demoType.value = 'album'
      demoTracks.value = normalizeDemoTracks(res.data)
    } else {
      const res = await API.preview(song)
      demoType.value = res.data.type || mediaType(song)
      demoTracks.value = normalizeDemoTracks(res.data)
    }
    activeDemoTrack.value = demoTracks.value[0] || song
    warmDemoAudio(activeDemoTrack.value)
    warmNextDemoTrack(activeDemoTrack.value)
  } catch (err) {
    demoType.value = mediaType(song)
    demoTracks.value = [song]
    activeDemoTrack.value = song
    if (!song) {
      demoError.value =
        err?.response?.data?.detail || err.message || t('search.previewError')
    }
  } finally {
    demoLoading.value = false
  }
}

function closeDemo() {
  demoOpen.value = false
  stopDemoPlayback()
}

function selectDemoTrack(track) {
  const wasPlaying = demoPlaying.value
  activeDemoTrack.value = track
  demoAudioError.value = ''
  stopDemoPlayback()
  warmDemoAudio(track)
  warmNextDemoTrack(track)
  if (wasPlaying) {
    toggleDemoPlay(track)
  }
}

async function toggleDemoPlay(track) {
  if (!track || demoAudioResolving.value) return

  const audioUrl = await audioUrlForDemoTrack(track)
  if (!audioUrl) {
    return
  }

  if (activeDemoTrack.value?.song_id === track.song_id && demoAudio.src) {
    if (demoPlaying.value) {
      demoAudio.pause()
      demoPlaying.value = false
    } else {
      await demoAudio.play()
      demoPlaying.value = true
      demoVolumeActive.value = true
    }
    return
  }

  activeDemoTrack.value = track
  demoAudio.pause()
  demoAudio.src = audioUrl
  demoAudio.currentTime = 0
  demoProgress.value = 0
  try {
    await demoAudio.play()
    demoPlaying.value = true
    demoVolumeActive.value = true
  } catch (err) {
    demoAudioError.value = err.message || 'Preview playback failed.'
    demoPlaying.value = false
  }
}

function stopDemoPlayback() {
  demoAudio.pause()
  demoAudio.src = ''
  demoPlaying.value = false
  demoProgress.value = 0
}

function seekDemo(value) {
  if (!activeDemoAudioUrl.value) return
  demoAudio.currentTime = Number(value)
  demoProgress.value = Number(value)
}

function setDemoVolume(value) {
  const volume = Math.min(1, Math.max(0, Number(value)))
  demoVolume.value = volume
  demoAudio.volume = volume
}

function downloadFromDemo() {
  if (!activeDemoTrack.value) return
  download(activeDemoTrack.value)
}

function downloadAlbumFromDemo() {
  if (!demoSourceItem.value) return
  download(demoSourceItem.value)
}

function demoTrackKey(track) {
  if (!track) return ''
  return String(track.song_id || track.url || `${track.name || ''}:${artistsOf(track)}`)
}

async function audioUrlForDemoTrack(track) {
  if (!track) return ''
  activeDemoTrack.value = track
  demoAudioError.value = ''

  if (track.preview_url) return track.preview_url

  const key = demoTrackKey(track)
  if (resolvedDemoAudioUrls.value[key]) return resolvedDemoAudioUrls.value[key]

  const inflight = resolvingDemoAudioKeys.value[key]
  if (inflight) return inflight

  demoAudioResolving.value = true
  try {
    return await resolveDemoAudio(track, key)
  } catch (err) {
    demoAudioError.value =
      err?.response?.data?.detail || err.message || 'Preview playback failed.'
    return ''
  } finally {
    demoAudioResolving.value = false
  }
}

function warmDemoAudio(track) {
  if (!track || track.preview_url) return

  const key = demoTrackKey(track)
  if (resolvedDemoAudioUrls.value[key] || resolvingDemoAudioKeys.value[key]) {
    return
  }

  resolveDemoAudio(track, key).catch((err) => {
    console.log('Preview warmup failed:', err.message)
  })
}

function warmNextDemoTrack(track) {
  if (demoType.value !== 'album' || !track) return
  const currentIndex = demoTracks.value.findIndex(
    (item) => demoTrackKey(item) === demoTrackKey(track)
  )
  const nextTrack = demoTracks.value[currentIndex + 1]
  if (nextTrack) warmDemoAudio(nextTrack)
}

async function resolveDemoAudio(track, key = demoTrackKey(track)) {
  if (!track) return ''
  if (resolvedDemoAudioUrls.value[key]) return resolvedDemoAudioUrls.value[key]
  if (resolvingDemoAudioKeys.value[key]) {
    return resolvingDemoAudioKeys.value[key]
  }

  const request = API.audioPreview(track)
    .then((res) => {
      const audioUrl = res.data?.audio_url || ''
      if (!audioUrl) throw new Error('No playable preview was found.')
      resolvedDemoAudioUrls.value = {
        ...resolvedDemoAudioUrls.value,
        [key]: audioUrl,
      }
      return audioUrl
    })
    .finally(() => {
      const { [key]: _done, ...remaining } = resolvingDemoAudioKeys.value
      resolvingDemoAudioKeys.value = remaining
    })

  resolvingDemoAudioKeys.value = {
    ...resolvingDemoAudioKeys.value,
    [key]: request,
  }
  return request
}

function normalizeDemoTracks(payload) {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.tracks)) return payload.tracks
  return []
}

function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00'
  const minutes = Math.floor(seconds / 60)
  const remaining = Math.floor(seconds % 60)
  return `${minutes}:${remaining.toString().padStart(2, '0')}`
}

</script>

<style scoped>
.demo-modal-enter-active,
.demo-modal-leave-active {
  transition: opacity 0.2s ease;
}
.demo-modal-enter-from,
.demo-modal-leave-to {
  opacity: 0;
}
.demo-modal-enter-active > div,
.demo-modal-leave-active > div {
  transition:
    transform 0.2s ease,
    opacity 0.2s ease;
}
.demo-modal-enter-from > div,
.demo-modal-leave-to > div {
  transform: translateY(16px);
  opacity: 0;
}
</style>
