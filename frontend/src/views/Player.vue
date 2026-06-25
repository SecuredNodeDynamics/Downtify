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
              :class="{ 'pulse-glow': player.isPlaying.value }"
            >
              <CoverImage
                v-if="
                  currentCoverSources.src ||
                  currentCoverSources.fallbacks.length
                "
                :key="
                  player.currentTrack.value?.file ||
                  libraryItems[0]?.file ||
                  'player-cover'
                "
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
                {{ trackArtist }}
              </p>
            </div>

            <!-- Progress -->
            <div class="mt-3 w-full sm:mt-6">
              <div
                class="player-progress"
                :class="{ 'player-progress--scrubbing': isScrubbing }"
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
                :disabled="files.length === 0"
              >
                <Icon
                  icon="clarity:step-forward-2-line"
                  class="h-5 w-5 -scale-x-100"
                />
              </button>
              <button
                class="player-play-btn inline-flex items-center justify-center rounded-full bg-primary text-primary-content shadow-glow-sm transition hover:scale-105 active:scale-95 disabled:opacity-50"
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
                :disabled="files.length === 0"
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
            </div>

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

        <!-- Library browser -->
        <aside
          class="panel-glow-shell panel-glow-shell-grow surface min-h-0 rounded-3xl"
        >
          <div
            class="player-queue panel-glow-inner flex flex-col gap-3 p-3 sm:gap-3 sm:p-5"
          >
            <div class="player-browse-chrome shrink-0 space-y-2 sm:space-y-3">
              <button
                v-if="canBrowseBack"
                type="button"
                class="inline-flex max-w-full items-center gap-1 rounded-full bg-white/5 px-3 py-1.5 text-xs font-medium text-primary"
                @click="browseBack"
              >
                <Icon
                  icon="clarity:arrow-line"
                  class="h-3.5 w-3.5 -scale-x-100"
                />
                <span class="truncate">{{ browseBackLabel }}</span>
              </button>

              <div
                v-if="!canBrowseBack"
                class="player-browse-tabs"
                role="tablist"
                :aria-label="t('player.browse')"
              >
                <button
                  v-for="tab in browseTabs"
                  :key="tab.id"
                  type="button"
                  role="tab"
                  class="player-browse-tab-btn"
                  :class="
                    browseMode === tab.id
                      ? 'player-browse-tab-btn-active'
                      : 'player-browse-tab-btn-inactive'
                  "
                  :aria-selected="browseMode === tab.id"
                  @click="setBrowseMode(tab.id)"
                >
                  {{ tab.shortLabel }}
                </button>
              </div>

              <form class="player-browse-search" @submit.prevent>
                <div class="relative min-w-0 flex-1">
                  <input
                    v-model="browseSearchQuery"
                    type="text"
                    inputmode="search"
                    enterkeyhint="search"
                    autocomplete="off"
                    autocapitalize="off"
                    autocorrect="off"
                    spellcheck="false"
                    class="input-modern h-12 w-full text-sm"
                    :placeholder="t('player.browseSearchPlaceholder')"
                    :aria-label="t('player.browseSearchPlaceholder')"
                  />
                  <button
                    type="submit"
                    class="absolute right-1.5 top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-primary text-primary-content shadow-glow-sm"
                    :disabled="!browseFilter"
                  >
                    <Icon icon="clarity:search-line" class="h-4 w-4" />
                  </button>
                </div>
              </form>
            </div>

            <div class="player-browse-body min-h-0 flex-1 overflow-y-auto">
              <div
                v-if="loading && libraryItems.length === 0"
                class="player-browse-grid"
              >
                <div
                  v-for="n in 6"
                  :key="n"
                  class="skeleton aspect-[4/5] rounded-2xl"
                />
              </div>

              <ul
                v-else-if="browseView === 'artists'"
                class="player-browse-grid"
              >
                <li
                  v-for="artist in filteredArtists"
                  :key="artist.name"
                  class="browse-tile-shell"
                >
                  <article
                    class="player-browse-card"
                    role="button"
                    tabindex="0"
                    @click="openArtist(artist.name)"
                    @keydown.enter="openArtist(artist.name)"
                    @keydown.space.prevent="openArtist(artist.name)"
                  >
                    <div class="player-browse-card-cover">
                      <CoverImage
                        v-if="
                          artistCoverFor(artist).src ||
                          artistCoverFor(artist).fallbacks.length
                        "
                        :key="`artist:${artist.name}`"
                        :src="artistCoverFor(artist).src"
                        :fallbacks="artistCoverFor(artist).fallbacks"
                        :alt="artist.name"
                        img-class="absolute inset-0 h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:user-line"
                            class="absolute left-1/2 top-1/2 h-8 w-8 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                          />
                        </template>
                      </CoverImage>
                      <Icon
                        v-else
                        icon="clarity:user-line"
                        class="absolute left-1/2 top-1/2 h-8 w-8 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                      />
                      <button
                        type="button"
                        class="player-browse-card-play"
                        :title="t('library.playArtist')"
                        @click.stop="playFiles(artist.files)"
                      >
                        <Icon icon="clarity:play-line" class="h-4 w-4" />
                      </button>
                    </div>
                    <div class="player-browse-card-body">
                      <p class="player-browse-card-title">{{ artist.name }}</p>
                      <p class="player-browse-card-sub">
                        {{
                          t('library.artistMeta', {
                            tracks: artist.files.length,
                            albums: artist.albumCount,
                          })
                        }}
                      </p>
                    </div>
                  </article>
                </li>
              </ul>

              <ul
                v-else-if="
                  browseView === 'albums' || browseView === 'artist-albums'
                "
                class="player-browse-grid"
              >
                <li
                  v-for="album in visibleAlbums"
                  :key="album.key"
                  class="browse-tile-shell"
                >
                  <article
                    class="player-browse-card"
                    role="button"
                    tabindex="0"
                    @click="openAlbum(album.key)"
                    @keydown.enter="openAlbum(album.key)"
                    @keydown.space.prevent="openAlbum(album.key)"
                  >
                    <div class="player-browse-card-cover">
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
                            class="absolute left-1/2 top-1/2 h-8 w-8 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                          />
                        </template>
                      </CoverImage>
                      <button
                        type="button"
                        class="player-browse-card-play"
                        :title="t('library.playAlbum')"
                        @click.stop="playFiles(album.files)"
                      >
                        <Icon icon="clarity:play-line" class="h-4 w-4" />
                      </button>
                    </div>
                    <div class="player-browse-card-body">
                      <p class="player-browse-card-title">{{ album.name }}</p>
                      <p class="player-browse-card-sub">{{ album.artist }}</p>
                      <p class="player-browse-card-meta">
                        {{
                          t('library.albumMeta', { tracks: album.files.length })
                        }}
                      </p>
                    </div>
                  </article>
                </li>
              </ul>

              <ul
                v-else-if="browseView === 'genres'"
                class="player-browse-grid"
              >
                <li
                  v-for="genre in filteredGenres"
                  :key="genre.name"
                  class="browse-tile-shell"
                >
                  <article
                    class="player-browse-card"
                    role="button"
                    tabindex="0"
                    @click="openGenre(genre.name)"
                    @keydown.enter="openGenre(genre.name)"
                    @keydown.space.prevent="openGenre(genre.name)"
                  >
                    <div class="player-browse-card-cover">
                      <GenreCover
                        :name="genre.name"
                        :files="genre.coverFiles"
                      />
                      <button
                        type="button"
                        class="player-browse-card-play"
                        :title="t('library.playGenre')"
                        @click.stop="playFiles(genre.files)"
                      >
                        <Icon icon="clarity:play-line" class="h-4 w-4" />
                      </button>
                    </div>
                    <div class="player-browse-card-body">
                      <p class="player-browse-card-title">{{ genre.name }}</p>
                      <p
                        v-if="genre.subgenres?.length"
                        class="player-browse-card-sub truncate"
                      >
                        {{ genre.subgenres.slice(0, 3).join(' · ') }}
                      </p>
                      <p class="player-browse-card-meta">
                        {{
                          t('player.genreMeta', { count: genre.files.length })
                        }}
                      </p>
                    </div>
                  </article>
                </li>
              </ul>

              <ul
                v-else-if="
                  browseView === 'tracks' && visibleTrackItems.length > 0
                "
                class="player-browse-grid"
              >
                <li
                  v-for="item in visibleTrackItems"
                  :key="item.file"
                  class="browse-tile-shell"
                >
                  <button
                    type="button"
                    class="player-browse-card"
                    :class="{
                      'player-browse-card-active': isCurrentFile(item.file),
                    }"
                    @click="playFiles(visibleTrackFiles, item.file)"
                  >
                    <div
                      class="player-browse-card-cover"
                      :class="{
                        'ring-2 ring-primary/50': isCurrentFile(item.file),
                      }"
                    >
                      <CoverImage
                        :key="item.file"
                        :src="coverSourcesFor(item.file).src"
                        :fallbacks="coverSourcesFor(item.file).fallbacks"
                        :alt="item.title"
                        img-class="absolute inset-0 h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:music-note-line"
                            class="absolute left-1/2 top-1/2 h-8 w-8 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                          />
                        </template>
                      </CoverImage>
                      <span
                        v-if="
                          isCurrentFile(item.file) && player.isPlaying.value
                        "
                        class="absolute bottom-2 right-2 equalizer h-4"
                        aria-hidden="true"
                      >
                        <span></span><span></span><span></span>
                      </span>
                    </div>
                    <div class="player-browse-card-body">
                      <p class="player-browse-card-title">{{ item.title }}</p>
                      <p class="player-browse-card-sub">
                        {{ item.artist || t('common.unknownArtist') }}
                        <span v-if="item.album"> · {{ item.album }}</span>
                      </p>
                    </div>
                  </button>
                </li>
              </ul>

              <div v-else-if="browseFilter && playerBrowseEmptyWithFilter">
                <ServerConnectionPrompt v-if="needsServerConnection()" />
                <LibraryDownloadOffers
                  v-else
                  :items="playerOnlineResults"
                  :loading="playerOnlineLoading"
                  :error="playerOnlineError"
                  @download="queueOnlineDownload"
                />
              </div>

              <div v-else-if="browseFilter" class="py-10 text-center">
                <p class="text-sm text-base-content/50">
                  {{ t('player.noFilterResults') }}
                </p>
              </div>

              <div v-else class="py-10 text-center">
                <p class="text-sm text-base-content/50">
                  {{ t('player.empty') }}
                </p>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, onActivated, computed, watch } from 'vue'
import { Icon } from '@iconify/vue'
import Navbar from '/src/components/Navbar.vue'
import CoverImage from '/src/components/CoverImage.vue'
import GenreCover from '/src/components/GenreCover.vue'
import LibraryDownloadOffers from '/src/components/LibraryDownloadOffers.vue'
import ServerConnectionPrompt from '/src/components/ServerConnectionPrompt.vue'
import API from '/src/model/api'
import { beginAppLoading, endAppLoading } from '/src/model/appLoading'
import { useDownloadManager } from '/src/model/download'
import {
  groupAlbums,
  groupArtists,
  groupGenres,
  matchesLibraryAlbumEntry,
  matchesLibraryArtistName,
  matchesLibraryGenreName,
  matchesLibraryTrackItem,
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
import { useMobileSearch } from '/src/model/mobileSearch'
import { useLibraryOnlineSearch } from '/src/model/libraryOnlineSearch'
import { useSearchManager } from '/src/model/search'
import { needsServerConnection } from '/src/model/serverConnection'
import { buildApiBaseUrl, getServerConfig } from '/src/model/serverConnection'
import { useI18n } from '/src/i18n'

defineOptions({ name: 'Player' })

const playerServerKey = buildApiBaseUrl(getServerConfig())
const initialPlayerSnapshot = getInitialLibrarySnapshot(playerServerKey)

const { t } = useI18n()
const player = usePlayer()
const mobileSearch = useMobileSearch()
const libraryFilter = mobileSearch.libraryFilter
const browseSearchQuery = ref(libraryFilter.value || '')
const browseFilter = computed(() => browseSearchQuery.value.trim())
const dm = useDownloadManager()
const sm = useSearchManager()

const files = ref(initialPlayerSnapshot.paths)
const libraryItems = ref(initialPlayerSnapshot.items)
const loading = ref(!initialPlayerSnapshot.ready)
const browseMode = ref('artists')
const selectedArtistName = ref('')
const selectedAlbumKey = ref('')
const selectedGenreName = ref('')
const progressBar = ref(null)
const progressTrack = ref(null)
const isScrubbing = ref(false)
const scrubPct = ref(0)
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
const genres = computed(() =>
  groupGenres(
    libraryItems.value,
    unknownGenreLabel.value,
    libraryGroupOptions.value
  )
)

const browseTabs = computed(() => [
  {
    id: 'artists',
    label: t('library.artists'),
    shortLabel: t('library.artists'),
  },
  {
    id: 'albums',
    label: t('library.albums'),
    shortLabel: t('library.albums'),
  },
  {
    id: 'tracks',
    label: t('library.tracks'),
    shortLabel: t('library.tracks'),
  },
  {
    id: 'genres',
    label: t('player.genres'),
    shortLabel: t('player.genresShort'),
  },
])

const selectedArtist = computed(() =>
  artists.value.find((artist) => artist.name === selectedArtistName.value)
)

const selectedAlbum = computed(() =>
  albums.value.find((album) => album.key === selectedAlbumKey.value)
)

const artistAlbums = computed(() =>
  albums.value.filter((album) => album.artist === selectedArtistName.value)
)

const browseView = computed(() => {
  if (selectedAlbumKey.value) return 'tracks'
  if (selectedGenreName.value) return 'tracks'
  if (selectedArtistName.value) {
    return artistAlbums.value.length > 0 ? 'artist-albums' : 'tracks'
  }
  if (browseMode.value === 'artists') return 'artists'
  if (browseMode.value === 'albums') return 'albums'
  if (browseMode.value === 'genres') return 'genres'
  return 'tracks'
})

const filteredArtists = computed(() => {
  const q = browseFilter.value
  if (!q) return artists.value
  return artists.value.filter((artist) =>
    matchesLibraryArtistName(artist.name, q)
  )
})

const visibleAlbums = computed(() => {
  const source =
    browseView.value === 'artist-albums' ? artistAlbums.value : albums.value
  const q = browseFilter.value
  if (!q) return source
  return source.filter((album) => matchesLibraryAlbumEntry(album, q))
})

const filteredGenres = computed(() => {
  const q = browseFilter.value
  const source = q
    ? genres.value.filter((genre) => matchesLibraryGenreName(genre.name, q))
    : genres.value
  const unknown = unknownGenreLabel.value
  const tagged = source.filter((genre) => genre.name !== unknown)
  return tagged.length > 0 ? tagged : source
})

const visibleTrackItems = computed(() => {
  let items = libraryItems.value

  if (selectedAlbum.value) {
    const allowed = new Set(selectedAlbum.value.files)
    items = items.filter((item) => allowed.has(item.file))
  } else if (selectedArtistName.value) {
    items = items.filter((item) => item.artist === selectedArtistName.value)
  } else if (selectedGenreName.value) {
    items = items.filter((item) => {
      const genre = item.browse_genre || item.genre || unknownGenreLabel.value
      return genre === selectedGenreName.value
    })
  }

  const q = browseFilter.value
  if (q) {
    items = items.filter((item) => matchesLibraryTrackItem(item, q))
  }

  return items
})

const visibleTrackFiles = computed(() =>
  visibleTrackItems.value.map((item) => item.file)
)

const playerBrowseEmptyWithFilter = computed(() => {
  if (!browseFilter.value) return false
  if (browseView.value === 'artists') return filteredArtists.value.length === 0
  if (browseView.value === 'albums' || browseView.value === 'artist-albums') {
    return visibleAlbums.value.length === 0
  }
  if (browseView.value === 'genres') return filteredGenres.value.length === 0
  return visibleTrackItems.value.length === 0
})

const playerOnlineSearchEnabled = computed(
  () =>
    Boolean(browseFilter.value) &&
    playerBrowseEmptyWithFilter.value &&
    !needsServerConnection() &&
    !sm.isValidURL(browseFilter.value)
)

const {
  results: playerOnlineResults,
  loading: playerOnlineLoading,
  error: playerOnlineError,
} = useLibraryOnlineSearch(browseFilter, browseView, playerOnlineSearchEnabled)

function queueOnlineDownload(song) {
  dm.queue(song)
}

const canBrowseBack = computed(() =>
  Boolean(
    selectedAlbumKey.value ||
      selectedArtistName.value ||
      selectedGenreName.value
  )
)

const browseBackLabel = computed(() => {
  if (selectedAlbumKey.value)
    return selectedArtistName.value || t('library.albums')
  if (selectedGenreName.value) return t('player.genres')
  return t('library.backToArtists')
})

const currentCoverSources = computed(() => {
  const file =
    player.currentTrack.value?.file || libraryItems.value[0]?.file || ''
  if (!file) return API.coverSourcesForFile('')
  return API.coverSourcesForFile(file)
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
  const list = (fileList || []).filter(Boolean)
  if (!list.length) return

  const currentFile = player.currentTrack.value?.file
  if (currentFile && list.includes(currentFile)) {
    player.setPlaylist(list, {
      startIndex: list.indexOf(currentFile),
      autoplay: false,
    })
    return
  }

  if (player.playlist.value.length === 0 || player.currentIndex.value < 0) {
    player.setPlaylist(list, { selectFirst: true })
  }
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
  } else if (player.currentIndex.value < 0 && files.value.length > 0) {
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
      syncPlayerPlaylist(items.map((item) => item.file))
      scheduleGenreRefresh(items)
    } else if (items.length > 0) {
      scheduleGenreRefresh(items)
    }
  } catch {
    // Ignore background refresh failures.
  }
}

function libraryItemsUnchanged(nextItems) {
  const current = libraryItems.value
  if (nextItems.length !== current.length) return false
  const currentByFile = new Map(current.map((item) => [item.file, item]))
  return nextItems.every((item) => {
    const existing = currentByFile.get(item.file)
    if (!existing) return false
    return (
      existing.title === item.title &&
      existing.artist === item.artist &&
      existing.album === item.album &&
      existing.genre === item.genre &&
      existing.browse_genre === item.browse_genre
    )
  })
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
    if (player.currentIndex.value < 0 && files.value.length > 0) {
      syncPlayerPlaylist(files.value)
    }
  }

  if (countUnknownGenres(libraryItems.value) > 0) {
    scheduleGenreRefresh(libraryItems.value)
  }
}

function setBrowseMode(mode) {
  browseMode.value = mode
  selectedArtistName.value = ''
  selectedAlbumKey.value = ''
  selectedGenreName.value = ''
}

function openArtist(name) {
  selectedArtistName.value = name
  selectedAlbumKey.value = ''
  selectedGenreName.value = ''
}

function openAlbum(key) {
  const album = albums.value.find((entry) => entry.key === key)
  selectedAlbumKey.value = key
  selectedArtistName.value = album?.artist || ''
  selectedGenreName.value = ''
}

function openGenre(name) {
  selectedGenreName.value = name
  selectedArtistName.value = ''
  selectedAlbumKey.value = ''
}

function browseBack() {
  if (selectedAlbumKey.value) {
    selectedAlbumKey.value = ''
    return
  }
  if (selectedGenreName.value) {
    selectedGenreName.value = ''
    return
  }
  selectedArtistName.value = ''
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

  browseMode.value = state.browseMode
  selectedArtistName.value = state.selectedArtistName
  selectedAlbumKey.value = state.selectedAlbumKey
  selectedGenreName.value = state.selectedGenreName
  playFiles(state.playlistFiles, state.startFile)
}

function isCurrentFile(file) {
  return player.currentTrack.value?.file === file
}

function clearBrowseSearch() {
  browseSearchQuery.value = ''
  mobileSearch.clearLibraryFilter()
}

watch(libraryFilter, (value) => {
  if (value !== browseSearchQuery.value.trim()) {
    browseSearchQuery.value = value
  }
})

watch(browseSearchQuery, (value) => {
  const trimmed = value.trim()
  if (trimmed === libraryFilter.value) return
  if (trimmed) mobileSearch.setLibraryFilter(trimmed)
  else mobileSearch.clearLibraryFilter()
})

function clearLibraryFilter() {
  clearBrowseSearch()
}

const trackTitle = computed(() => {
  const c = player.currentTrack.value
  if (c?.title) return c.title
  const first = libraryItems.value[0]
  if (first?.title) return first.title
  return t('player.empty')
})

const trackArtist = computed(() => {
  const c = player.currentTrack.value
  if (c?.artist) return c.artist
  if (c) return t('common.unknownArtist')
  const first = libraryItems.value[0]
  if (first?.artist) return first.artist
  return ''
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

  .player-queue {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    min-height: 0;
  }

  .player-browse-body {
    flex: 1 1 auto;
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

  .player-queue {
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

.player-browse-tabs {
  @apply inline-flex min-w-0 w-full gap-1 overflow-x-auto rounded-full border border-white/10 bg-base-100/75 p-1;
}

.player-browse-tab-btn {
  @apply flex-1 whitespace-nowrap rounded-full px-2 py-2 text-center text-xs font-medium transition-colors sm:px-3 sm:text-sm;
}

.player-browse-tab-btn-active {
  @apply bg-primary text-primary-content shadow-glow-sm;
}

.player-browse-tab-btn-inactive {
  @apply text-base-content/60 hover:text-base-content;
}

.player-browse-search {
  @apply flex w-full items-center;
}

.player-browse-body {
  @apply min-h-0 flex-1 overflow-x-hidden overflow-y-auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.player-browse-body::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.player-browse-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.player-browse-card {
  @apply flex h-full w-full cursor-pointer flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/5 text-left transition-colors active:bg-white/10;
}

.player-browse-card-active {
  @apply border-primary/30 bg-primary/10;
}

.player-browse-card-cover {
  @apply relative aspect-square w-full shrink-0 overflow-hidden bg-primary/10;
}

.player-browse-card-play {
  @apply absolute bottom-2 right-2 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-content shadow-glow-sm transition-transform active:scale-95;
}

.player-browse-card-body {
  @apply p-2.5;
}

.player-browse-card-title {
  @apply truncate text-sm font-semibold leading-snug;
}

.player-browse-card-sub {
  @apply mt-0.5 line-clamp-2 text-[11px] leading-4 text-base-content/50;
}

.player-browse-card-meta {
  @apply mt-0.5 text-[11px] text-base-content/40;
}

@media (min-width: 1024px) {
  .player-browse-grid {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .player-browse-card {
    @apply flex-row items-center gap-3 rounded-xl border-transparent bg-transparent p-2 active:bg-white/10;
  }

  .player-browse-card-cover {
    @apply aspect-auto h-11 w-11 rounded-xl;
  }

  .player-browse-card-play {
    @apply static shrink-0;
  }

  .player-browse-card-body {
    @apply min-w-0 flex-1 p-0;
  }

  .player-browse-card-sub,
  .player-browse-card-meta {
    @apply line-clamp-1;
  }
}
</style>
