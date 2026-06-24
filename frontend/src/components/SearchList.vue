<template>
  <div class="mx-auto max-w-4xl px-4 py-4 sm:py-8 sm:px-6 overflow-x-hidden">
    <!-- Header -->
    <div class="mb-6 sm:mb-8 mobile-page-header">
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
      <div v-if="sm.searchTerm.value" class="mt-4 max-w-md">
        <SearchResultFilter />
      </div>
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
      <p class="text-base-content/50 text-sm">
        {{ hasUnfilteredResults ? emptyFilterMessage : t('search.empty') }}
      </p>
      <p class="text-base-content/40 text-xs mt-1">
        {{
          hasUnfilteredResults
            ? t('search.emptyFilterHint')
            : t('search.emptyHint')
        }}
      </p>
    </div>

    <!-- Results -->
    <ul v-else class="space-y-2">
      <li
        v-for="(song, index) in paginatedData"
        :key="song.song_id || index"
        class="surface rounded-2xl p-3 sm:p-4 flex flex-col gap-3 sm:flex-row sm:items-center"
      >
        <div class="flex min-w-0 flex-1 items-center gap-3 sm:gap-4">
          <!-- Cover -->
          <div class="track-cover w-14 sm:w-16">
            <CoverImage
              v-if="song.cover_url"
              :src="coverSrc(song.cover_url)"
              :alt="song.name"
              img-class="h-full w-full object-cover"
            >
              <template #fallback>
                <div
                  class="h-full w-full flex items-center justify-center text-base-content/30"
                >
                  <Icon icon="clarity:music-note-line" class="h-6 w-6" />
                </div>
              </template>
            </CoverImage>
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
        </div>

        <!-- Actions -->
        <div
          class="flex flex-wrap items-center justify-end gap-1 border-t border-white/6 pt-2 sm:border-0 sm:pt-0 shrink-0"
        >
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
            v-if="externalServiceUrl(song)"
            class="icon-btn"
            :href="externalServiceUrl(song)"
            target="_blank"
            rel="noopener"
            :title="externalServiceLabel(song)"
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
        v-for="(page, index) in visiblePages"
        :key="`${page}-${index}`"
        class="h-10 min-w-[2.5rem] rounded-full px-3 text-sm font-medium transition-colors"
        :class="
          page === currentPage
            ? 'bg-primary text-primary-content shadow-glow-sm'
            : page === '…'
            ? 'cursor-default text-base-content/30'
            : 'text-base-content/70 hover:text-base-content hover:bg-white/10'
        "
        :disabled="page === '…'"
        @click="page !== '…' && (currentPage = page)"
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
            class="surface-strong w-full max-w-3xl overflow-hidden rounded-t-3xl shadow-2xl sm:rounded-3xl"
          >
            <div
              class="flex items-center justify-between border-b border-white/5 px-5 py-4"
            >
              <div class="min-w-0">
                <p
                  class="text-xs font-semibold uppercase tracking-wider text-base-content/50"
                >
                  {{ demoTypeLabel }}
                </p>
                <h2 class="truncate text-lg font-bold tracking-tight">
                  {{ demoTitle }}
                </h2>
              </div>
              <button
                class="icon-btn shrink-0"
                @click="closeDemo"
                :title="t('common.close')"
              >
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
                <div
                  class="relative aspect-square overflow-hidden rounded-2xl bg-base-content/10 shadow-lg"
                >
                  <CoverImage
                    v-if="activeDemoTrack?.cover_url"
                    :src="coverSrc(activeDemoTrack?.cover_url)"
                    :alt="activeDemoTrack.name"
                    img-class="h-full w-full object-cover"
                  >
                    <template #fallback>
                      <div
                        class="flex h-full w-full items-center justify-center text-base-content/30"
                      >
                        <Icon
                          icon="clarity:music-note-line"
                          class="h-12 w-12"
                        />
                      </div>
                    </template>
                  </CoverImage>
                  <div
                    v-else
                    class="flex h-full w-full items-center justify-center text-base-content/30"
                  >
                    <Icon icon="clarity:music-note-line" class="h-12 w-12" />
                  </div>
                  <button
                    class="absolute inset-0 flex items-center justify-center transition disabled:cursor-not-allowed"
                    :class="activeDemoPlayButtonClass"
                    :disabled="isDemoPlayDisabled(activeDemoTrack)"
                    @click="toggleDemoPlay(activeDemoTrack)"
                    :title="playButtonTitle"
                  >
                    <Icon
                      :icon="playIconForTrack(activeDemoTrack)"
                      class="h-12 w-12 drop-shadow"
                      :class="demoPlayIconClass(activeDemoTrack, 'text-white')"
                    />
                  </button>
                </div>

                <div class="min-w-0">
                  <h3 class="truncate text-xl font-bold">
                    {{ activeDemoTrack?.name }}
                  </h3>
                  <p class="truncate text-sm text-base-content/60">
                    {{ activeDemoTrack ? artistsOf(activeDemoTrack) : '' }}
                  </p>
                  <p
                    v-if="activeDemoTrack?.album_name"
                    class="mt-1 truncate text-xs text-base-content/40"
                  >
                    {{ activeDemoTrack.album_name }}
                    <span v-if="activeDemoTrack.year">
                      · {{ activeDemoTrack.year }}</span
                    >
                  </p>

                  <div class="mt-5 flex items-center gap-2">
                    <span
                      class="w-9 text-right text-xs tabular-nums text-base-content/40"
                    >
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
                    <div ref="demoVolumeRoot" class="relative shrink-0">
                      <button
                        class="icon-btn h-8 w-8 text-base-content/60 hover:text-base-content"
                        :class="{
                          'bg-white/10 text-base-content': demoVolumeOpen,
                        }"
                        type="button"
                        :aria-label="t('player.volume')"
                        :aria-expanded="demoVolumeOpen"
                        @click="toggleDemoVolume"
                      >
                        <Icon :icon="demoVolumeIcon" class="h-4 w-4" />
                      </button>
                      <div
                        v-if="demoVolumeOpen"
                        class="absolute bottom-full right-0 z-20 mb-2 flex flex-col items-center gap-1 rounded-2xl border border-white/10 bg-base-100/95 px-3 py-3 text-base-content/60 shadow-2xl backdrop-blur"
                        @pointerdown.stop
                      >
                        <span class="text-[10px] tabular-nums leading-none">
                          {{ Math.round(demoVolume * 100) }}
                        </span>
                        <div class="volume-slider-shell">
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            :value="demoVolume"
                            class="volume-slider-vertical"
                            :aria-label="t('player.volume')"
                            @input="setDemoVolume($event.target.value)"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <p
                    v-if="isDemoTrackResolving(activeDemoTrack)"
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
                    v-else-if="
                      !isDemoTrackReady(activeDemoTrack) &&
                      !isDemoTrackFailed(activeDemoTrack)
                    "
                    class="mt-3 text-xs italic text-base-content/40"
                  >
                    Preview will be available shortly.
                  </p>

                  <div
                    class="mt-5 flex flex-wrap items-center gap-2 lg:flex-nowrap"
                  >
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
                      v-if="externalServiceUrl(activeDemoTrack)"
                      class="btn btn-sm gap-2 rounded-full bg-base-100/85"
                      :class="externalServiceButtonClass(activeDemoTrack)"
                      :href="externalServiceUrl(activeDemoTrack)"
                      target="_blank"
                      rel="noopener"
                    >
                      <Icon icon="clarity:pop-out-line" class="h-4 w-4" />
                      {{ externalServiceLabel(activeDemoTrack) }}
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
                  :class="{
                    'bg-primary/10 text-primary':
                      activeDemoTrack?.song_id === track.song_id,
                  }"
                  @click="selectDemoTrack(track)"
                  role="button"
                  tabindex="0"
                  @keydown.enter.prevent="selectDemoTrack(track)"
                  @keydown.space.prevent="selectDemoTrack(track)"
                >
                  <CoverImage
                    v-if="track.cover_url"
                    :src="coverSrc(track.cover_url)"
                    :alt="track.name"
                    img-class="h-10 w-10 shrink-0 rounded-lg object-cover"
                  >
                    <template #fallback>
                      <div
                        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-base-content/10"
                      >
                        <Icon icon="clarity:music-note-line" class="h-4 w-4" />
                      </div>
                    </template>
                  </CoverImage>
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
                    :class="isDemoTrackFailed(track) ? 'text-error' : ''"
                    :disabled="isDemoPlayDisabled(track)"
                    @click.stop="toggleDemoPlay(track)"
                    :title="playButtonTitle"
                  >
                    <Icon
                      :icon="playIconForTrack(track)"
                      class="h-4 w-4"
                      :class="demoPlayIconClass(track)"
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

const DEMO_VOLUME_KEY = 'downtify-player-volume'
import { Icon } from '@iconify/vue'

import { useSearchManager } from '../model/search'
import { useProgressTracker, useDownloadManager } from '../model/download'
import { useI18n } from '../i18n'
import API from '../model/api'
import CoverImage from './CoverImage.vue'
import SearchResultFilter from './SearchResultFilter.vue'

const PAGE_SIZE = 5

const props = defineProps(['data', 'error'])
const emit = defineEmits(['download'])

const sm = useSearchManager()
const pt = useProgressTracker()
const dm = useDownloadManager()
const { t } = useI18n()

function coverSrc(url) {
  return API.mediaUrl(url)
}

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
const demoVolumeRoot = ref(null)
const demoVolume = ref(
  parseFloat(localStorage.getItem(DEMO_VOLUME_KEY) || '0.85')
)
const demoVolumeOpen = ref(false)
const resolvedDemoAudioUrls = ref({})
const resolvingDemoAudioKeys = ref({})
const failedDemoAudioKeys = ref({})
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
  document.removeEventListener('pointerdown', onDemoVolumeOutsideClick)
  stopDemoPlayback()
})

watch(demoVolumeOpen, (open) => {
  if (open) {
    document.addEventListener('pointerdown', onDemoVolumeOutsideClick)
  } else {
    document.removeEventListener('pointerdown', onDemoVolumeOutsideClick)
  }
})

const totalPages = computed(() =>
  Math.ceil((props.data?.length || 0) / PAGE_SIZE)
)

const visiblePages = computed(() => {
  const pages = totalPages.value
  if (pages <= 9) {
    return Array.from({ length: pages }, (_, index) => index + 1)
  }

  const middle = new Set([
    currentPage.value - 1,
    currentPage.value,
    currentPage.value + 1,
  ])
  const visible = [1]
  let previous = 1

  for (let page = 2; page < pages; page += 1) {
    if (page <= 3 || page >= pages - 2 || middle.has(page)) {
      if (page - previous > 1) visible.push('…')
      visible.push(page)
      previous = page
    }
  }

  if (pages - previous > 1) visible.push('…')
  visible.push(pages)
  return visible
})

const paginatedData = computed(() => {
  if (!props.data) return []
  const start = (currentPage.value - 1) * PAGE_SIZE
  return props.data.slice(start, start + PAGE_SIZE)
})

const hasUnfilteredResults = computed(
  () => (sm.results.value?.length || 0) > 0 && (props.data?.length || 0) === 0
)

const emptyFilterMessage = computed(() => {
  if (sm.resultFilter.value === 'albums') return t('search.emptyAlbums')
  if (sm.resultFilter.value === 'tracks') return t('search.emptyTracks')
  return t('search.empty')
})

const demoTypeLabel = computed(() =>
  demoType.value === 'album' ? t('search.albumType') : t('search.trackType')
)

const demoTitle = computed(() => {
  const first = demoTracks.value[0]
  if (demoType.value === 'album') return first?.album_name || first?.name || ''
  return first?.name || ''
})

const activeDemoAudioUrl = computed(() =>
  playableAudioUrlForTrack(activeDemoTrack.value)
)

const playButtonTitle = computed(() =>
  demoPlaying.value ? t('player.pause') : t('player.play')
)

const activeDemoPlayButtonClass = computed(() => {
  if (isDemoTrackFailed(activeDemoTrack.value)) {
    return 'bg-error/20 hover:bg-error/25 opacity-100'
  }
  if (isDemoPlayDisabled(activeDemoTrack.value)) {
    return 'bg-black/25 opacity-55'
  }
  return 'bg-black/35 hover:bg-black/45'
})

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

watch(
  () => sm.resultFilter.value,
  () => {
    currentPage.value = 1
  }
)

watch(totalPages, (pages) => {
  if (pages > 0 && currentPage.value > pages) {
    currentPage.value = pages
  }
})

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

function isSpotifyUrl(url) {
  return /open\.spotify\.com\//.test(url || '')
}

function isYoutubeMusicUrl(url) {
  return /(?:music\.youtube\.com|youtube\.com|youtu\.be)\//.test(url || '')
}

function youtubeMusicUrlFor(item) {
  if (!item) return ''
  if (isYoutubeMusicUrl(item.url)) return item.url
  if (item.browse_id)
    return `https://music.youtube.com/browse/${item.browse_id}`

  const youtubeId =
    item.youtube_id ||
    (item.source === 'youtube' ? item.song_id : '') ||
    item.url?.match(/[?&]v=([A-Za-z0-9_-]{6,})/)?.[1] ||
    item.url?.match(/youtu\.be\/([A-Za-z0-9_-]{6,})/)?.[1]

  if (youtubeId && !String(youtubeId).startsWith('album:')) {
    return `https://music.youtube.com/watch?v=${youtubeId}`
  }
  return ''
}

function externalServiceUrl(item) {
  if (!item) return ''
  if (isSpotifyUrl(item.url)) return item.url
  if (
    item.source === 'youtube' ||
    isYoutubeMusicUrl(item.url) ||
    item.browse_id
  ) {
    return youtubeMusicUrlFor(item)
  }
  return item.url || ''
}

function externalServiceLabel(item) {
  return isSpotifyUrl(externalServiceUrl(item))
    ? t('search.openOnSpotify')
    : t('search.openOnYoutubeMusic')
}

function externalServiceButtonClass(item) {
  return isSpotifyUrl(externalServiceUrl(item))
    ? 'border-white/10'
    : 'border-error/70 text-error hover:border-error hover:bg-error/10'
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
  demoVolumeOpen.value = false
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
    warmDemoAudio(activeDemoTrack.value)
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
  demoVolumeOpen.value = false
  stopDemoPlayback()
}

function selectDemoTrack(track) {
  const wasPlaying = demoPlaying.value
  activeDemoTrack.value = track
  demoAudioError.value = ''
  demoVolumeOpen.value = false
  stopDemoPlayback()
  warmDemoAudio(track)
  warmNextDemoTrack(track)
  if (wasPlaying) {
    toggleDemoPlay(track)
  }
}

async function toggleDemoPlay(track) {
  if (!track || isDemoPlayDisabled(track)) return

  const audioUrl = await audioUrlForDemoTrack(track)
  if (!isValidMediaUrl(audioUrl)) {
    return
  }

  if (
    demoTrackKey(activeDemoTrack.value) === demoTrackKey(track) &&
    demoAudio.src
  ) {
    if (demoPlaying.value) {
      demoAudio.pause()
      demoPlaying.value = false
    } else {
      await demoAudio.play()
      demoPlaying.value = true
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
  } catch (err) {
    demoAudioError.value = err.message || 'Preview playback failed.'
    demoPlaying.value = false
  }
}

function stopDemoPlayback() {
  demoAudio.pause()
  demoAudio.removeAttribute('src')
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
  try {
    localStorage.setItem(DEMO_VOLUME_KEY, String(volume))
  } catch {
    // ignore
  }
}

function toggleDemoVolume() {
  demoVolumeOpen.value = !demoVolumeOpen.value
}

function onDemoVolumeOutsideClick(event) {
  if (!demoVolumeOpen.value) return
  if (demoVolumeRoot.value?.contains(event.target)) return
  demoVolumeOpen.value = false
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
  return String(
    track.song_id || track.url || `${track.name || ''}:${artistsOf(track)}`
  )
}

function playableAudioUrlForTrack(track) {
  if (!track) return ''
  if (isValidMediaUrl(track.preview_url)) return track.preview_url
  const resolvedUrl = resolvedDemoAudioUrls.value[demoTrackKey(track)]
  return isValidMediaUrl(resolvedUrl) ? resolvedUrl : ''
}

function isDemoTrackReady(track) {
  if (!track) return false
  return Boolean(playableAudioUrlForTrack(track))
}

function isDemoTrackResolving(track) {
  if (!track || isValidMediaUrl(track.preview_url)) return false
  return Boolean(resolvingDemoAudioKeys.value[demoTrackKey(track)])
}

function isDemoTrackFailed(track) {
  if (!track || isValidMediaUrl(track.preview_url)) return false
  return Boolean(failedDemoAudioKeys.value[demoTrackKey(track)])
}

function isDemoPlayDisabled(track) {
  if (!track) return true
  if (isDemoTrackFailed(track)) return true
  if (isDemoTrackResolving(track)) return true
  return !isDemoTrackReady(track)
}

function playIconForTrack(track) {
  if (isDemoTrackFailed(track)) return 'clarity:times-circle-solid'
  if (isDemoTrackResolving(track)) return 'clarity:refresh-line'
  if (
    demoTrackKey(activeDemoTrack.value) === demoTrackKey(track) &&
    demoPlaying.value
  ) {
    return 'clarity:pause-solid'
  }
  return 'clarity:play-solid'
}

function demoPlayIconClass(track, defaultClass = '') {
  if (isDemoTrackFailed(track)) return 'text-error'
  return [
    defaultClass,
    isDemoTrackResolving(track) ? 'animate-spin text-primary' : '',
  ]
}

async function audioUrlForDemoTrack(track) {
  if (!track) return ''
  activeDemoTrack.value = track
  demoAudioError.value = ''

  if (isValidMediaUrl(track.preview_url)) return track.preview_url

  const key = demoTrackKey(track)
  if (resolvedDemoAudioUrls.value[key]) return resolvedDemoAudioUrls.value[key]
  if (failedDemoAudioKeys.value[key]) return ''

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
  if (!track || isValidMediaUrl(track.preview_url)) return

  const key = demoTrackKey(track)
  if (
    resolvedDemoAudioUrls.value[key] ||
    resolvingDemoAudioKeys.value[key] ||
    failedDemoAudioKeys.value[key]
  ) {
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
      if (!isValidMediaUrl(audioUrl)) {
        throw new Error('No playable preview was found.')
      }
      const { [key]: _failed, ...remainingFailures } = failedDemoAudioKeys.value
      failedDemoAudioKeys.value = remainingFailures
      resolvedDemoAudioUrls.value = {
        ...resolvedDemoAudioUrls.value,
        [key]: audioUrl,
      }
      return audioUrl
    })
    .catch((err) => {
      const message =
        err?.response?.data?.detail || err.message || 'Preview playback failed.'
      failedDemoAudioKeys.value = {
        ...failedDemoAudioKeys.value,
        [key]: message,
      }
      if (demoTrackKey(activeDemoTrack.value) === key) {
        demoAudioError.value = message
      }
      throw err
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

function isValidMediaUrl(value) {
  if (typeof value !== 'string') return false
  const trimmed = value.trim()
  return /^https?:\/\//.test(trimmed) || trimmed.startsWith('blob:')
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
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.demo-modal-enter-from > div,
.demo-modal-leave-to > div {
  transform: translateY(16px);
  opacity: 0;
}

.volume-slider-shell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 5.5rem;
}

.volume-slider-vertical {
  -webkit-appearance: none;
  appearance: none;
  width: 5.5rem;
  height: 0.25rem;
  margin: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15);
  cursor: pointer;
  outline: none;
  transform: rotate(-90deg);
  transform-origin: center;
}

[data-theme='downtify-light'] .volume-slider-vertical {
  background: rgba(0, 0, 0, 0.12);
}

.volume-slider-vertical::-webkit-slider-runnable-track {
  height: 0.25rem;
  border-radius: 999px;
  background: transparent;
}

.volume-slider-vertical::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 0.75rem;
  height: 0.75rem;
  margin-top: -0.25rem;
  border-radius: 999px;
  background: #1ad05c;
  box-shadow: 0 0 10px rgba(26, 208, 92, 0.45);
  cursor: pointer;
}

.volume-slider-vertical::-moz-range-track {
  height: 0.25rem;
  border-radius: 999px;
  background: transparent;
}

.volume-slider-vertical::-moz-range-thumb {
  width: 0.75rem;
  height: 0.75rem;
  border: none;
  border-radius: 999px;
  background: #1ad05c;
  box-shadow: 0 0 10px rgba(26, 208, 92, 0.45);
  cursor: pointer;
}
</style>
