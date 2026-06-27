<template>
  <div class="player-view min-h-0 overflow-x-hidden">
    <Navbar />

    <div
      class="player-page mx-auto flex w-full max-w-5xl min-h-0 flex-1 flex-col px-4 py-2 sm:px-6 sm:py-8"
    >
      <!-- Header -->
      <div class="mb-4 sm:mb-8 mobile-page-header shrink-0">
        <h1 class="text-2xl font-bold tracking-tight">
          {{ t('player.title') }}
        </h1>
        <p class="mt-1 text-sm text-base-content/60">
          {{ t('player.subtitle') }}
        </p>
      </div>

      <!-- Empty state -->
      <div
        v-if="files.length === 0 && !loading"
        class="surface rounded-2xl p-12 flex flex-col items-center text-center"
      >
        <Icon
          icon="clarity:headphones-line"
          class="h-12 w-12 text-base-content/20 mb-4"
        />
        <p class="text-base-content/50 text-sm">{{ t('player.empty') }}</p>
        <p class="text-base-content/40 text-xs mt-1">
          {{ t('player.emptyHint') }}
        </p>
      </div>

      <!-- Skeleton -->
      <div
        v-else-if="loading && files.length === 0 && libraryItems.length === 0"
        class="space-y-3"
      >
        <div class="skeleton h-52 rounded-3xl lg:h-72" />
        <div class="skeleton h-16 rounded-2xl" />
        <div class="skeleton h-16 rounded-2xl" />
      </div>

      <!-- Player + queue -->
      <div v-else class="player-shell min-h-0 flex-1">
        <!-- Now playing -->
        <section class="panel-glow-shell surface shrink-0 grow-0 rounded-3xl">
          <div
            class="player-now flex flex-col items-center rounded-3xl p-3 text-center sm:p-8"
          >
            <!-- Cover -->
            <div
              class="player-cover relative flex items-center justify-center overflow-hidden rounded-2xl bg-primary/10 text-primary shadow-glow sm:rounded-3xl"
              :class="{
                'pulse-glow': hasActiveTrack && player.isPlaying.value,
                'opacity-80': !hasActiveTrack,
              }"
            >
              <CoverImage
                v-if="
                  hasActiveTrack &&
                  (currentCoverSources.src ||
                    currentCoverSources.fallbacks.length)
                "
                :key="player.currentTrack.value?.file || 'player-cover'"
                :src="currentCoverSources.src"
                :fallbacks="currentCoverSources.fallbacks"
                :alt="trackTitle"
                img-class="absolute inset-0 h-full w-full object-cover"
              >
                <template #fallback>
                  <Icon
                    icon="clarity:music-note-line"
                    class="h-16 w-16 sm:h-24 sm:w-24"
                  />
                </template>
              </CoverImage>
              <Icon
                v-else
                icon="clarity:music-note-line"
                class="h-16 w-16 sm:h-24 sm:w-24"
              />
              <div
                v-if="player.isPlaying.value"
                class="absolute bottom-2 right-2 equalizer h-5 sm:bottom-3 sm:right-3"
                aria-hidden="true"
              >
                <span></span><span></span><span></span>
              </div>
            </div>

            <!-- Title / artist -->
            <div class="mt-3 w-full sm:mt-6">
              <p class="text-lg font-bold tracking-tight truncate sm:text-xl">
                {{ trackTitle }}
              </p>
              <p class="mt-0.5 text-sm text-base-content/60 truncate">
                <span v-if="trackArtist">{{ trackArtist }}</span>
                <span v-else-if="!hasActiveTrack" class="text-base-content/40">
                  {{ t('player.nothingPlayingHint') }}
                </span>
              </p>
            </div>

            <!-- Progress -->
            <div class="mt-3 w-full sm:mt-6">
              <div
                class="player-progress"
                :class="{
                  'player-progress--scrubbing': isScrubbing,
                  'pointer-events-none opacity-50': !hasActiveTrack,
                }"
                ref="progressBar"
                role="slider"
                tabindex="0"
                :aria-label="t('player.seek')"
                :aria-valuemin="0"
                :aria-valuemax="Math.floor(player.duration.value || 0)"
                :aria-valuenow="Math.floor(player.currentTime.value || 0)"
                :aria-valuetext="`${formatTime(
                  player.currentTime.value
                )} / ${formatTime(player.duration.value)}`"
                @pointerdown="onSeekStart"
                @keydown="onSeekKeydown"
              >
                <div class="player-progress-track" ref="progressTrack">
                  <div
                    class="player-progress-fill"
                    :style="{ width: `${displayProgressPct}%` }"
                  />
                  <div
                    class="player-progress-thumb"
                    :style="{ left: `${displayProgressPct}%` }"
                  />
                </div>
              </div>
              <div
                class="mt-1 flex items-center justify-between text-xs text-base-content/50 tabular-nums sm:mt-2"
              >
                <span>{{ formatTime(player.currentTime.value) }}</span>
                <span>{{ formatTime(player.duration.value) }}</span>
              </div>
            </div>

            <!-- Transport -->
            <div
              class="mt-3 flex items-center justify-center gap-2 sm:mt-5 sm:gap-3"
            >
              <button
                class="icon-btn h-9 w-9 sm:h-10 sm:w-10"
                :class="{ 'icon-btn-active': player.shuffle.value }"
                @click="player.toggleShuffle()"
                :title="
                  player.shuffle.value
                    ? t('player.shuffleOn')
                    : t('player.shuffleOff')
                "
              >
                <Icon
                  icon="clarity:shuffle-line"
                  class="h-4 w-4 sm:h-5 sm:w-5"
                />
              </button>
              <button
                class="icon-btn h-10 w-10 sm:h-10 sm:w-10"
                @click="player.prev()"
                :title="t('player.previous')"
                :disabled="!hasActiveTrack"
              >
                <Icon
                  icon="clarity:step-forward-2-line"
                  class="h-5 w-5 -scale-x-100"
                />
              </button>
              <button
                class="player-play-btn inline-flex items-center justify-center rounded-full shadow-glow-sm transition hover:scale-105 active:scale-95 disabled:opacity-50"
                :class="
                  player.isPlaying.value
                    ? 'bg-amber-300 text-amber-950 hover:bg-amber-200'
                    : 'bg-primary text-primary-content'
                "
                @click="player.toggle()"
                :disabled="files.length === 0"
                :title="
                  player.isPlaying.value ? t('player.pause') : t('player.play')
                "
              >
                <Icon
                  :icon="
                    player.isPlaying.value
                      ? 'clarity:pause-solid'
                      : 'clarity:play-solid'
                  "
                  class="h-7 w-7 sm:h-6 sm:w-6"
                />
              </button>
              <button
                class="icon-btn h-10 w-10 sm:h-10 sm:w-10"
                @click="player.next()"
                :title="t('player.next')"
                :disabled="!hasActiveTrack"
              >
                <Icon icon="clarity:step-forward-2-line" class="h-5 w-5" />
              </button>
              <button
                class="icon-btn relative h-9 w-9 sm:h-10 sm:w-10"
                :class="{
                  'icon-btn-active': player.repeatMode.value !== 'off',
                }"
                @click="player.cycleRepeat()"
                :title="repeatTitle"
              >
                <Icon
                  icon="clarity:refresh-line"
                  class="h-4 w-4 sm:h-5 sm:w-5"
                />
                <span
                  v-if="player.repeatMode.value === 'one'"
                  class="absolute -bottom-0.5 -right-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-primary px-1 text-[9px] font-bold text-primary-content"
                >
                  1
                </span>
              </button>
              <button
                v-if="lyricsAvailable"
                class="icon-btn h-9 w-9 sm:h-10 sm:w-10"
                :class="{ 'icon-btn-active': lyricsOpen }"
                @click="lyricsOpen = !lyricsOpen"
                :title="t('player.lyrics')"
              >
                <Icon
                  icon="clarity:music-note-line"
                  class="h-4 w-4 sm:h-5 sm:w-5"
                />
              </button>
            </div>

            <section
              v-if="lyricsAvailable && lyricsOpen"
              class="lyrics-preview mt-4 w-full rounded-2xl border border-white/10 bg-base-100/55 p-3 text-left sm:mt-5 sm:p-4"
            >
              <div class="mb-2 flex items-center justify-between gap-3">
                <h2
                  class="text-xs font-semibold uppercase tracking-wider text-base-content/45"
                >
                  {{ t('player.lyrics') }}
                </h2>
                <div class="flex items-center gap-1.5">
                  <span class="text-xs tabular-nums text-base-content/40">
                    {{ formatTime(player.currentTime.value) }}
                  </span>
                  <div
                    v-if="syncedLyrics.length"
                    class="lyrics-offset-controls"
                    :aria-label="t('player.lyricsOffset')"
                  >
                    <button
                      type="button"
                      class="lyrics-offset-btn"
                      :title="t('player.lyricsEarlier')"
                      @click="adjustLyricsOffset(-0.1)"
                    >
                      <Icon icon="clarity:minus-line" class="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      class="lyrics-offset-value"
                      :title="t('player.lyricsReset')"
                      @click="resetLyricsOffset"
                    >
                      {{ lyricsOffsetLabel }}
                    </button>
                    <button
                      type="button"
                      class="lyrics-offset-btn"
                      :title="t('player.lyricsLater')"
                      @click="adjustLyricsOffset(0.1)"
                    >
                      <Icon icon="clarity:plus-line" class="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>
              <div
                v-if="syncedLyrics.length"
                ref="lyricsScroller"
                class="lyrics-scroll"
              >
                <p
                  v-for="(line, index) in syncedLyrics"
                  :key="`${line.time}:${index}`"
                  :ref="(el) => setLyricLineRef(el, index)"
                  class="lyrics-line"
                  :class="{ 'lyrics-line-active': index === activeLyricIndex }"
                >
                  {{ line.text }}
                </p>
              </div>
              <p v-else class="lyrics-plain">
                {{ lyricsPlain }}
              </p>
            </section>

            <!-- Volume (desktop only — mobile uses device volume) -->
            <div class="mt-6 hidden w-full max-w-xs items-center gap-3 lg:flex">
              <button
                class="icon-btn"
                @click="player.toggleMute()"
                :title="
                  player.isMuted.value ? t('player.unmute') : t('player.mute')
                "
              >
                <Icon
                  :icon="
                    player.isMuted.value || player.volume.value === 0
                      ? 'clarity:volume-mute-line'
                      : player.volume.value < 0.5
                      ? 'clarity:volume-down-line'
                      : 'clarity:volume-up-line'
                  "
                  class="h-5 w-5"
                />
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                :value="player.isMuted.value ? 0 : player.volume.value"
                @input="onVolume($event)"
                class="player-range flex-1"
                :title="t('player.volume')"
              />
            </div>
          </div>
        </section>

        <!-- Artist & album details -->
        <aside
          class="panel-glow-shell panel-glow-shell-grow surface min-h-0 rounded-3xl"
        >
          <div
            class="player-details flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-3 sm:gap-5 sm:p-5"
          >
            <template
              v-if="
                hasActiveTrack &&
                (currentArtistEntry || currentArtistAlbums.length)
              "
            >
              <section v-if="currentArtistEntry" class="space-y-2">
                <h2 class="player-detail-heading">
                  {{ t('library.artists') }}
                </h2>
                <article class="player-detail-card">
                  <div class="player-detail-main">
                    <div class="player-detail-cover">
                      <CoverImage
                        v-if="
                          artistCoverFor(currentArtistEntry).src ||
                          artistCoverFor(currentArtistEntry).fallbacks.length
                        "
                        :key="`player-artist:${currentArtistEntry.name}`"
                        :src="artistCoverFor(currentArtistEntry).src"
                        :fallbacks="
                          artistCoverFor(currentArtistEntry).fallbacks
                        "
                        :alt="currentArtistEntry.name"
                        img-class="absolute inset-0 h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:user-line"
                            class="absolute left-1/2 top-1/2 h-7 w-7 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                          />
                        </template>
                      </CoverImage>
                      <Icon
                        v-else
                        icon="clarity:user-line"
                        class="absolute left-1/2 top-1/2 h-7 w-7 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                      />
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="player-detail-title">
                        {{ currentArtistEntry.name }}
                      </p>
                      <p class="player-detail-meta">
                        {{
                          t('library.artistMeta', {
                            tracks: currentArtistEntry.files.length,
                            albums: currentArtistEntry.albumCount,
                          })
                        }}
                      </p>
                    </div>
                  </div>
                  <div class="player-detail-actions">
                    <button
                      type="button"
                      class="btn btn-primary btn-sm inline-flex h-9 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-3 sm:px-4"
                      @click="playFiles(currentArtistEntry.files)"
                    >
                      <Icon icon="clarity:play-line" class="h-4 w-4 shrink-0" />
                      {{ t('library.playArtist') }}
                    </button>
                    <LibraryArtistMonitor
                      :artist-name="currentArtistEntry.name"
                    />
                  </div>
                </article>
              </section>

              <section v-if="currentArtistAlbums.length" class="space-y-2">
                <h2 class="player-detail-heading">{{ t('library.albums') }}</h2>
                <article
                  v-for="album in currentArtistAlbums"
                  :key="album.key"
                  class="player-detail-card"
                  :class="{
                    'player-detail-card-active': album.key === currentAlbumKey,
                  }"
                >
                  <div class="player-detail-main">
                    <div class="player-detail-cover">
                      <CoverImage
                        :key="album.coverFile"
                        :src="coverSourcesFor(album.coverFile).src"
                        :fallbacks="coverSourcesFor(album.coverFile).fallbacks"
                        :alt="album.name"
                        img-class="absolute inset-0 h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:album-line"
                            class="absolute left-1/2 top-1/2 h-7 w-7 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                          />
                        </template>
                      </CoverImage>
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="player-detail-title">{{ album.name }}</p>
                      <p class="player-detail-meta">
                        {{
                          t('library.albumMeta', {
                            tracks: album.files.length,
                          })
                        }}
                      </p>
                    </div>
                  </div>
                  <div class="player-detail-actions">
                    <button
                      type="button"
                      class="btn btn-primary btn-sm inline-flex h-9 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-3 sm:px-4"
                      @click="playFiles(album.files)"
                    >
                      <Icon icon="clarity:play-line" class="h-4 w-4 shrink-0" />
                      {{ t('library.playAlbum') }}
                    </button>
                  </div>
                </article>
              </section>
            </template>

            <div
              v-else
              class="flex flex-1 items-center justify-center py-10 text-center"
            >
              <p class="text-sm text-base-content/50">
                {{ t('player.detailsEmpty') }}
              </p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ref,
  onMounted,
  onUnmounted,
  onActivated,
  computed,
  watch,
  nextTick,
} from 'vue'
import { Icon } from '@iconify/vue'
import Navbar from '/src/components/Navbar.vue'
import CoverImage from '/src/components/CoverImage.vue'
import LibraryArtistMonitor from '/src/components/LibraryArtistMonitor.vue'
import API from '/src/model/api'
import { beginAppLoading, endAppLoading } from '/src/model/appLoading'
import {
  albumKey,
  groupAlbums,
  groupArtists,
  libraryItemsEqual,
  normalizeLibraryItem,
} from '/src/model/library'
import {
  fetchLibraryItems,
  getInitialLibrarySnapshot,
  onLibraryChanged,
} from '/src/model/librarySession'
import { usePlayer, formatTime, trackInfoFromFile } from '/src/model/player'
import {
  consumePlayerNavigation,
  resolvePlayerBrowseState,
} from '/src/model/playerNavigation'
import { buildApiBaseUrl, getServerConfig } from '/src/model/serverConnection'
import { useI18n } from '/src/i18n'

defineOptions({ name: 'Player' })

const LYRICS_OFFSET_KEY = 'downtify-player-lyrics-offset'

const playerServerKey = buildApiBaseUrl(getServerConfig())
const initialPlayerSnapshot = getInitialLibrarySnapshot(playerServerKey)

const { t } = useI18n()
const player = usePlayer()

const files = ref(initialPlayerSnapshot.paths)
const libraryItems = ref(initialPlayerSnapshot.items)
const loading = ref(!initialPlayerSnapshot.ready)
const progressBar = ref(null)
const progressTrack = ref(null)
const isScrubbing = ref(false)
const scrubPct = ref(0)
const lyricsOpen = ref(false)
const lyricsLoading = ref(false)
const syncedLyrics = ref([])
const lyricsPlain = ref('')
const lyricsScroller = ref(null)
const lyricLineRefs = ref([])
const lyricsOffset = ref(readLyricsOffset())
let lyricsRequestSeq = 0
let seekRaf = 0
let pendingSeekRatio = null

const displayProgressPct = computed(() =>
  isScrubbing.value ? scrubPct.value : player.progressPct.value
)
let genreRefreshTimers = []
let stopLibraryListener = null

const unknownGenreLabel = computed(() => t('player.unknownGenre'))
const libraryGroupOptions = computed(() => ({
  unknownArtist: t('common.unknownArtist'),
}))

const artists = computed(() =>
  groupArtists(libraryItems.value, libraryGroupOptions.value)
)
const albums = computed(() =>
  groupAlbums(libraryItems.value, libraryGroupOptions.value)
)

const hasActiveTrack = computed(
  () => player.currentIndex.value >= 0 && !!player.currentTrack.value
)

const lyricsAvailable = computed(
  () => syncedLyrics.value.length > 0 || Boolean(lyricsPlain.value)
)

const syncedLyricsTime = computed(() =>
  Math.max(0, player.currentTime.value + lyricsOffset.value)
)

const lyricsOffsetLabel = computed(() => {
  const offset = lyricsOffset.value
  if (Math.abs(offset) < 0.05) return '0.0s'
  return `${offset > 0 ? '+' : ''}${offset.toFixed(1)}s`
})

const activeLyricIndex = computed(() => {
  const lines = syncedLyrics.value
  if (!lines.length) return -1
  const current = syncedLyricsTime.value
  let active = 0
  for (let i = 0; i < lines.length; i += 1) {
    if (Number(lines[i]?.time || 0) > current) break
    active = i
  }
  return active
})

const currentLibraryItem = computed(() => {
  const file = player.currentTrack.value?.file
  if (!file) return null
  return libraryItems.value.find((item) => item.file === file) || null
})

function artistNamesMatch(a, b) {
  return (
    String(a || '')
      .trim()
      .toLocaleLowerCase() ===
    String(b || '')
      .trim()
      .toLocaleLowerCase()
  )
}

const currentArtistEntry = computed(() => {
  const name =
    currentLibraryItem.value?.artist || player.currentTrack.value?.artist || ''
  if (!name) return null
  return (
    artists.value.find((artist) => artistNamesMatch(artist.name, name)) || null
  )
})

const currentAlbumKey = computed(() => {
  const item = currentLibraryItem.value
  if (!item?.album) return ''
  return albumKey(item.artist, item.album)
})

const currentArtistAlbums = computed(() => {
  const entry = currentArtistEntry.value
  if (!entry) return []
  return albums.value.filter((album) =>
    artistNamesMatch(album.artist, entry.name)
  )
})

const currentCoverSources = computed(() => {
  const file = player.currentTrack.value?.file || ''
  const artist =
    currentLibraryItem.value?.artist || player.currentTrack.value?.artist || ''
  return API.coverSourcesForNowPlaying(file, { artistName: artist })
})

const artistCoverMap = computed(() => {
  const map = new Map()
  for (const artist of artists.value) {
    map.set(
      artist.name,
      API.coverSourcesForArtist(artist.name, artist.previewFiles)
    )
  }
  return map
})

function artistCoverFor(artist) {
  return artistCoverMap.value.get(artist?.name) || API.coverSourcesForArtist('')
}

function coverSourcesFor(file) {
  return API.coverSourcesForFile(file)
}

function readLyricsOffset() {
  try {
    const value = Number.parseFloat(
      localStorage.getItem(LYRICS_OFFSET_KEY) || '0'
    )
    return Number.isFinite(value) ? Math.max(-5, Math.min(5, value)) : 0
  } catch {
    return 0
  }
}

function persistLyricsOffset() {
  try {
    localStorage.setItem(LYRICS_OFFSET_KEY, lyricsOffset.value.toFixed(1))
  } catch {
    // Ignore private-mode storage errors.
  }
}

function adjustLyricsOffset(delta) {
  const next = Math.round((lyricsOffset.value + delta) * 10) / 10
  lyricsOffset.value = Math.max(-5, Math.min(5, next))
  persistLyricsOffset()
}

function resetLyricsOffset() {
  lyricsOffset.value = 0
  persistLyricsOffset()
}

function setLyricLineRef(el, index) {
  if (el) lyricLineRefs.value[index] = el
}

async function loadLyricsForFile(file) {
  lyricsRequestSeq += 1
  const seq = lyricsRequestSeq
  syncedLyrics.value = []
  lyricsPlain.value = ''
  lyricLineRefs.value = []
  lyricsLoading.value = Boolean(file)
  if (!file) {
    lyricsOpen.value = false
    lyricsLoading.value = false
    return
  }

  try {
    const res = await API.getLibraryLyrics(file)
    if (seq !== lyricsRequestSeq) return
    const data = res.data || {}
    syncedLyrics.value = Array.isArray(data.lines) ? data.lines : []
    lyricsPlain.value = syncedLyrics.value.length
      ? ''
      : String(data.plain || '').trim()
    if (!lyricsAvailable.value) lyricsOpen.value = false
  } catch {
    if (seq !== lyricsRequestSeq) return
    syncedLyrics.value = []
    lyricsPlain.value = ''
    lyricsOpen.value = false
  } finally {
    if (seq === lyricsRequestSeq) {
      lyricsLoading.value = false
    }
  }
}

function fallbackLibraryItems(paths) {
  const options = libraryGroupOptions.value
  return (paths || []).map((file) => {
    const info = trackInfoFromFile(file)
    return normalizeLibraryItem(
      {
        file,
        title: info.title,
        artist: info.artist,
        album: '',
        genre: '',
      },
      options
    )
  })
}

function syncPlayerPlaylist(fileList) {
  player.syncPlaylistFromFiles(fileList || [], { autoplay: false })
}

function libraryPathsUnchanged(nextItems) {
  const nextPaths = (nextItems || []).map((item) => item.file)
  if (nextPaths.length !== files.value.length) return false
  return nextPaths.every((file, index) => file === files.value[index])
}

function applyLibraryItems(items) {
  const options = libraryGroupOptions.value
  libraryItems.value = items.map((item) => normalizeLibraryItem(item, options))
  files.value = libraryItems.value.map((item) => item.file)
  API.warmLibraryCovers(libraryItems.value)
}

function hydrateLibraryFromSession() {
  const snapshot = getInitialLibrarySnapshot(playerServerKey)
  if (!snapshot.ready) return false

  libraryItems.value = snapshot.items.map((item) =>
    normalizeLibraryItem(item, libraryGroupOptions.value)
  )
  files.value = snapshot.paths

  if (player.playlist.value.length === 0 && files.value.length > 0) {
    syncPlayerPlaylist(files.value)
  } else if (player.currentTrack.value?.file && files.value.length > 0) {
    syncPlayerPlaylist(files.value)
  }

  API.warmLibraryCovers(libraryItems.value)
  return true
}

async function fetchPlayerLibraryItems(options = {}) {
  return fetchLibraryItems(
    () => API.getLibraryFiles().then((res) => res.data || []),
    options
  )
}

async function applyFetchedLibrary(items) {
  if (!items.length) {
    libraryItems.value = []
    files.value = []
    return
  }

  applyLibraryItems(items)
  syncPlayerPlaylist(items.map((item) => item.file))
}

async function refreshLibraryMetadataInBackground(force = false) {
  try {
    const items = await API.refreshLibraryInBackground(force)
    if (items.length > 0 && !libraryItemsUnchanged(items)) {
      applyLibraryItems(items)
      if (!libraryPathsUnchanged(items)) {
        syncPlayerPlaylist(items.map((item) => item.file))
      }
      scheduleGenreRefresh(items)
    } else if (items.length > 0) {
      scheduleGenreRefresh(items)
    }
  } catch {
    // Ignore background refresh failures.
  }
}

function libraryItemsUnchanged(nextItems) {
  const options = libraryGroupOptions.value
  const normalized = nextItems.map((item) =>
    normalizeLibraryItem(item, options)
  )
  return libraryItemsEqual(libraryItems.value, normalized)
}

function countUnknownGenres(items) {
  const label = unknownGenreLabel.value
  return (items || []).filter((item) => {
    const genre = String(item?.genre || '').trim()
    return !genre || genre === label
  }).length
}

function clearGenreRefreshTimers() {
  for (const timer of genreRefreshTimers) {
    clearTimeout(timer)
  }
  genreRefreshTimers = []
}

async function refreshLibraryMetadata() {
  await refreshLibraryMetadataInBackground()
}

async function refreshLibraryGenres() {
  await refreshLibraryMetadata()
}

function scheduleGenreRefresh(items) {
  clearGenreRefreshTimers()
  if (countUnknownGenres(items) === 0) return

  for (const delay of [3000, 10000, 30000, 90000, 300000]) {
    genreRefreshTimers.push(
      setTimeout(() => {
        refreshLibraryGenres()
      }, delay)
    )
  }
}

async function load({ background = false } = {}) {
  const hadCache =
    hydrateLibraryFromSession() ||
    files.value.length > 0 ||
    libraryItems.value.length > 0
  if (!background) {
    loading.value = !hadCache
    if (!hadCache) beginAppLoading()
  }

  try {
    const items = await fetchPlayerLibraryItems({
      preferPrefetch: !background,
    })
    await applyFetchedLibrary(items)
  } catch {
    try {
      const res = await API.listDownloads()
      const paths = res.data || []
      if (paths.length > 0) {
        applyLibraryItems(fallbackLibraryItems(paths))
        syncPlayerPlaylist(paths)
      } else {
        files.value = []
        libraryItems.value = []
      }
    } catch {
      if (!hadCache) {
        files.value = []
        libraryItems.value = []
      }
    }
  } finally {
    loading.value = false
    if (!background && !hadCache) endAppLoading()
    applyPlayerNavigationIntent()
    if (player.currentTrack.value?.file && files.value.length > 0) {
      syncPlayerPlaylist(files.value)
    }
  }

  if (countUnknownGenres(libraryItems.value) > 0) {
    scheduleGenreRefresh(libraryItems.value)
  }
}

function playFiles(fileList, startFile = null) {
  const list = fileList || []
  if (!list.length) return
  const startIndex = startFile ? Math.max(0, list.indexOf(startFile)) : 0
  player.setPlaylist(list, { startIndex })
}

function applyPlayerNavigationIntent() {
  const intent = consumePlayerNavigation()
  if (!intent) return

  const state = resolvePlayerBrowseState(
    libraryItems.value,
    intent,
    libraryGroupOptions.value
  )
  if (!state) return

  playFiles(state.playlistFiles, state.startFile)
}

const trackTitle = computed(() => {
  if (!hasActiveTrack.value) return t('player.nothingPlaying')
  return player.currentTrack.value?.title || t('player.empty')
})

const trackArtist = computed(() => {
  if (!hasActiveTrack.value) return ''
  const c = player.currentTrack.value
  if (c?.artist) return c.artist
  return t('common.unknownArtist')
})

const repeatTitle = computed(() => {
  if (player.repeatMode.value === 'one') return t('player.repeatOne')
  if (player.repeatMode.value === 'all') return t('player.repeatAll')
  return t('player.repeatOff')
})

function onVolume(e) {
  player.setVolume(parseFloat(e.target.value))
}

function ratioFromEvent(e) {
  const el = progressTrack.value || progressBar.value
  if (!el) return 0
  const rect = el.getBoundingClientRect()
  if (rect.width <= 0) return 0
  const x = (e.clientX ?? 0) - rect.left
  return Math.max(0, Math.min(1, x / rect.width))
}

function flushPendingSeek() {
  if (pendingSeekRatio === null) return
  player.seekRatio(pendingSeekRatio)
  pendingSeekRatio = null
}

function queueSeek(ratio) {
  pendingSeekRatio = ratio
  if (seekRaf) return
  seekRaf = requestAnimationFrame(() => {
    seekRaf = 0
    flushPendingSeek()
  })
}

function applyScrub(e, { commitAudio = true } = {}) {
  const ratio = ratioFromEvent(e)
  scrubPct.value = ratio * 100
  if (commitAudio) {
    queueSeek(ratio)
  }
}

function onSeekStart(e) {
  if (!hasActiveTrack.value) return
  if (e.pointerType === 'mouse' && e.button !== 0) return
  e.preventDefault()
  isScrubbing.value = true
  const el = progressBar.value
  if (el?.setPointerCapture) {
    try {
      el.setPointerCapture(e.pointerId)
    } catch {
      // ignore
    }
  }
  applyScrub(e)
  window.addEventListener('pointermove', onSeekDrag)
  window.addEventListener('pointerup', onSeekEnd)
  window.addEventListener('pointercancel', onSeekEnd)
}

function onSeekDrag(e) {
  if (!isScrubbing.value) return
  applyScrub(e)
}

function onSeekEnd(e) {
  if (!isScrubbing.value) return
  isScrubbing.value = false
  if (e) {
    applyScrub(e)
  }
  flushPendingSeek()
  window.removeEventListener('pointermove', onSeekDrag)
  window.removeEventListener('pointerup', onSeekEnd)
  window.removeEventListener('pointercancel', onSeekEnd)
  const el = progressBar.value
  if (el?.releasePointerCapture && e?.pointerId !== undefined) {
    try {
      el.releasePointerCapture(e.pointerId)
    } catch {
      // ignore
    }
  }
}

function onSeekKeydown(e) {
  if (!player.duration.value) return
  const step = e.shiftKey ? 10 : 5
  if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
    e.preventDefault()
    player.seek(Math.max(0, player.currentTime.value - step))
  } else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
    e.preventDefault()
    player.seek(
      Math.min(player.duration.value, player.currentTime.value + step)
    )
  } else if (e.key === 'Home') {
    e.preventDefault()
    player.seek(0)
  } else if (e.key === 'End') {
    e.preventDefault()
    player.seek(player.duration.value)
  }
}

watch(
  () => player.currentTrack.value?.file || '',
  (file) => {
    void loadLyricsForFile(file)
  },
  { immediate: true }
)

watch(activeLyricIndex, async (index) => {
  if (!lyricsOpen.value || index < 0) return
  await nextTick()
  lyricLineRefs.value[index]?.scrollIntoView({
    block: 'center',
    behavior: 'smooth',
  })
})

onMounted(() => {
  window.scroll(0, 0)
  if (libraryItems.value.length) {
    API.warmLibraryCovers(libraryItems.value)
    syncPlayerPlaylist(files.value)
  }
  load()
  stopLibraryListener = onLibraryChanged(() => {
    void refreshLibraryMetadataInBackground(true)
  })
})

onActivated(() => {
  if (libraryItems.value.length > 0) {
    syncPlayerPlaylist(files.value)
    applyPlayerNavigationIntent()
    void refreshLibraryMetadataInBackground()
    return
  }
  void load()
})

onUnmounted(() => {
  stopLibraryListener?.()
  clearGenreRefreshTimers()
  onSeekEnd()
  if (seekRaf) {
    cancelAnimationFrame(seekRaf)
    seekRaf = 0
  }
})
</script>

<style scoped>
.player-view {
  @apply flex min-h-0 flex-col overflow-x-hidden;
}

.lyrics-preview {
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.04);
}

.lyrics-scroll {
  max-height: clamp(7.5rem, 22dvh, 13rem);
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  scrollbar-width: none;
}

.lyrics-scroll::-webkit-scrollbar {
  display: none;
}

.lyrics-line {
  @apply py-1.5 text-center text-sm font-medium leading-snug text-base-content/40 transition-all duration-200 sm:text-base;
}

.lyrics-line-active {
  @apply text-primary;
  transform: scale(1.04);
  text-shadow: 0 0 18px rgb(var(--color-primary) / 0.24);
}

.lyrics-offset-controls {
  @apply flex h-7 items-center overflow-hidden rounded-full border border-white/10 bg-base-100/60 text-xs text-base-content/55;
}

.lyrics-offset-btn,
.lyrics-offset-value {
  @apply flex h-full items-center justify-center transition-colors hover:bg-primary/10 hover:text-primary focus-visible:bg-primary/10 focus-visible:text-primary focus-visible:outline-none;
}

.lyrics-offset-btn {
  @apply w-7;
}

.lyrics-offset-value {
  @apply min-w-12 px-2 font-medium tabular-nums;
}

.lyrics-plain {
  @apply max-h-40 overflow-y-auto whitespace-pre-line text-center text-sm leading-relaxed text-base-content/60;
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 1023px) {
  .player-view {
    height: calc(
      100dvh - var(--app-header-height) - var(--app-safe-top) -
        var(--app-bottom-nav-height) - var(--app-safe-bottom)
    );
    max-height: calc(
      100dvh - var(--app-header-height) - var(--app-safe-top) -
        var(--app-bottom-nav-height) - var(--app-safe-bottom)
    );
    overflow: hidden;
  }

  .player-page {
    min-height: 0;
  }

  .player-shell {
    display: flex;
    flex-direction: column;
    gap: 0.875rem;
    min-height: 0;
    flex: 1 1 auto;
  }

  .player-shell > .panel-glow-shell-grow {
    flex: 1 1 auto;
    min-height: 0;
  }

  .player-now {
    flex-shrink: 0;
  }

  .player-cover {
    width: min(28vw, 6.5rem);
    aspect-ratio: 1;
  }

  .player-play-btn {
    height: 3rem;
    width: 3rem;
  }

  .player-details {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    min-height: 0;
    overflow-x: hidden;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-y: contain;
  }
}

@media (min-width: 1024px) {
  .player-view {
    height: auto;
    max-height: none;
    overflow: visible;
  }

  .player-shell {
    display: grid;
    grid-template-columns: 1fr 360px;
    gap: 1.5rem;
  }

  .player-details {
    max-height: 640px;
  }

  .player-cover {
    height: 16rem;
    width: 16rem;
  }

  .player-play-btn {
    height: 3.5rem;
    width: 3.5rem;
  }
}

.player-progress {
  position: relative;
  width: 100%;
  padding: 0.875rem 0;
  cursor: pointer;
  touch-action: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  outline: none;
}

.player-progress:focus-visible .player-progress-track {
  box-shadow: 0 0 0 2px rgba(26, 208, 92, 0.35);
}

.player-progress-track {
  position: relative;
  height: 4px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
  transition: height 160ms ease;
}

[data-theme='downtify-light'] .player-progress-track {
  background: rgba(0, 0, 0, 0.1);
}

.player-progress:hover .player-progress-track,
.player-progress--scrubbing .player-progress-track {
  height: 6px;
}

.player-progress-fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: 9999px;
  background: #1ad05c;
  transition: width 100ms linear;
  will-change: width;
}

.player-progress-thumb {
  position: absolute;
  top: 50%;
  left: 0;
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
  transform: translate(-50%, -50%) scale(0.9);
  opacity: 0;
  transition: left 100ms linear, opacity 160ms ease, transform 160ms ease,
    width 160ms ease, height 160ms ease;
  will-change: left, transform;
}

.player-progress:hover .player-progress-thumb,
.player-progress--scrubbing .player-progress-thumb,
.player-progress:focus-visible .player-progress-thumb {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1);
}

.player-progress--scrubbing .player-progress-fill,
.player-progress--scrubbing .player-progress-thumb {
  transition: none;
}

@media (hover: none), (pointer: coarse) {
  .player-progress {
    padding: 1rem 0;
  }

  .player-progress-track {
    height: 5px;
  }

  .player-progress-thumb {
    opacity: 1;
    height: 18px;
    width: 18px;
    transform: translate(-50%, -50%) scale(1);
  }

  .player-progress--scrubbing .player-progress-thumb {
    height: 20px;
    width: 20px;
  }
}

.player-range {
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.1);
  height: 4px;
  border-radius: 9999px;
  outline: none;
}
[data-theme='downtify-light'] .player-range {
  background: rgba(0, 0, 0, 0.1);
}
.player-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  cursor: pointer;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
}
.player-range::-moz-range-thumb {
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  border: none;
  cursor: pointer;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
}
.pulse-glow {
  animation: glow 2.4s ease-in-out infinite;
}
@keyframes glow {
  0%,
  100% {
    box-shadow: 0 0 36px rgba(26, 208, 92, 0.3);
  }
  50% {
    box-shadow: 0 0 60px rgba(26, 208, 92, 0.55);
  }
}

.player-detail-heading {
  @apply text-xs font-semibold uppercase tracking-wide text-base-content/45;
}

.player-detail-card {
  @apply flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 sm:gap-4 sm:p-4;
}

.player-detail-card-active {
  @apply border-primary/30 bg-primary/10;
}

.player-detail-main {
  @apply flex min-w-0 items-start gap-3;
}

.player-detail-actions {
  @apply flex w-full flex-nowrap items-center justify-end gap-2;
}

.player-detail-cover {
  @apply relative h-16 w-16 shrink-0 overflow-hidden rounded-xl bg-primary/10;
}

.player-detail-title {
  @apply truncate text-base font-semibold leading-snug;
}

.player-detail-meta {
  @apply mt-0.5 text-xs text-base-content/50;
}

.player-detail-card :deep(.library-artist-monitor) {
  @apply shrink-0;
}

.player-detail-card :deep(.library-artist-monitor .btn) {
  @apply h-9 whitespace-nowrap;
}
</style>
