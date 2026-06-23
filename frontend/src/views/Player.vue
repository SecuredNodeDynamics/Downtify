<template>
  <div class="player-view min-h-0 overflow-x-hidden">
    <Navbar />

    <div
      class="player-page mx-auto flex w-full max-w-5xl flex-col px-4 py-2 sm:flex-1 sm:px-6 sm:py-8 min-h-0"
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
      <div v-else-if="loading && !player.currentTrack.value" class="space-y-3">
        <div class="skeleton h-52 rounded-3xl lg:h-72" />
        <div class="skeleton h-16 rounded-2xl" />
        <div class="skeleton h-16 rounded-2xl" />
      </div>

      <!-- Player + queue -->
      <div v-else class="player-shell min-h-0 lg:flex-1">
        <!-- Now playing -->
        <section class="player-now surface rounded-3xl p-3 sm:p-8 flex flex-col items-center text-center">
          <p
            class="mb-3 w-full text-left text-xs font-semibold uppercase tracking-wider text-base-content/50 lg:hidden"
          >
            {{ t('player.nowPlaying') }}
          </p>

          <!-- Cover -->
          <div
            class="player-cover relative flex items-center justify-center overflow-hidden rounded-2xl bg-primary/10 text-primary shadow-glow sm:rounded-3xl"
            :class="{ 'pulse-glow': player.isPlaying.value }"
          >
            <CoverImage
              v-if="currentCoverSources.src || currentCoverSources.fallbacks.length"
              :key="player.currentTrack.value?.file || 'player-cover'"
              :src="currentCoverSources.src"
              :fallbacks="currentCoverSources.fallbacks"
              :alt="player.currentTrack.value.title"
              img-class="absolute inset-0 h-full w-full object-cover"
            >
              <template #fallback>
                <Icon icon="clarity:music-note-line" class="h-16 w-16 sm:h-24 sm:w-24" />
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
              ref="progressBar"
              @click="onSeekClick"
              @pointerdown="onSeekStart"
            >
              <div class="player-progress-track">
                <div
                  class="player-progress-fill"
                  :style="`width: ${player.progressPct.value}%`"
                />
                <div
                  class="player-progress-thumb"
                  :style="`left: calc(${player.progressPct.value}% - 7px)`"
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
          <div class="mt-3 flex items-center justify-center gap-2 sm:mt-5 sm:gap-3">
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
              <Icon icon="clarity:shuffle-line" class="h-4 w-4 sm:h-5 sm:w-5" />
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
              :class="{ 'icon-btn-active': player.repeatMode.value !== 'off' }"
              @click="player.cycleRepeat()"
              :title="repeatTitle"
            >
              <Icon icon="clarity:refresh-line" class="h-4 w-4 sm:h-5 sm:w-5" />
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
        </section>

        <!-- Library browser -->
        <aside
          class="player-queue surface flex flex-col rounded-3xl p-3 sm:p-5 lg:max-h-[640px] lg:overflow-y-auto"
        >
          <div class="mb-2 flex items-center justify-between gap-2 px-1 sm:mb-3">
            <div class="min-w-0">
              <h2
                class="text-xs font-semibold uppercase tracking-wider text-base-content/50"
              >
                {{ browseHeading }}
              </h2>
              <p
                v-if="browseSubtitle"
                class="mt-0.5 truncate text-[11px] text-base-content/45"
              >
                {{ browseSubtitle }}
              </p>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <button
                v-if="browsePlayFiles.length"
                type="button"
                class="btn btn-primary btn-xs h-8 rounded-full px-3"
                @click="playFiles(browsePlayFiles)"
              >
                <Icon icon="clarity:play-line" class="h-3.5 w-3.5" />
                {{ t('player.playAll') }}
              </button>
              <span class="text-[11px] text-base-content/40">
                {{ browseCountText }}
              </span>
            </div>
          </div>

          <button
            v-if="canBrowseBack"
            type="button"
            class="mb-2 inline-flex max-w-full items-center gap-1 rounded-full bg-white/5 px-3 py-1.5 text-xs font-medium text-primary"
            @click="browseBack"
          >
            <Icon icon="clarity:arrow-line" class="h-3.5 w-3.5 -scale-x-100" />
            <span class="truncate">{{ browseBackLabel }}</span>
          </button>

          <div
            v-if="libraryFilter"
            class="mb-2 flex items-center gap-2 rounded-xl bg-primary/10 px-3 py-2 text-xs"
          >
            <Icon icon="clarity:search-line" class="h-4 w-4 shrink-0 text-primary" />
            <span class="min-w-0 flex-1 truncate text-base-content/80">
              {{ libraryFilter }}
            </span>
            <button
              type="button"
              class="shrink-0 font-medium text-primary"
              @click="clearLibraryFilter"
            >
              {{ t('player.clearFilter') }}
            </button>
          </div>

          <div
            v-if="!canBrowseBack"
            class="metadata-tab-shell metadata-filter-tab-shell player-browse-tabs tab-glow-shell"
          >
            <button
              v-for="tab in browseTabs"
              :key="tab.id"
              type="button"
              class="metadata-tab-btn"
              :class="
                browseMode === tab.id
                  ? 'bg-primary text-primary-content shadow-glow-sm'
                  : 'text-base-content/60 hover:text-base-content'
              "
              @click="setBrowseMode(tab.id)"
            >
              <span class="sm:hidden">{{ tab.shortLabel }}</span>
              <span class="hidden sm:inline">{{ tab.label }}</span>
            </button>
          </div>

          <div class="player-browse-body min-h-0 flex-1 overflow-y-auto">
            <div
              v-if="loading && libraryItems.length === 0"
              class="player-browse-grid"
            >
              <div v-for="n in 6" :key="n" class="skeleton aspect-[4/5] rounded-2xl" />
            </div>

            <ul
              v-else-if="browseView === 'artists'"
              class="player-browse-grid"
            >
              <li v-for="artist in filteredArtists" :key="artist.name">
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
                      v-if="artistCoverFor(artist).src || artistCoverFor(artist).fallbacks.length"
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
              v-else-if="browseView === 'albums' || browseView === 'artist-albums'"
              class="player-browse-grid"
            >
              <li
                v-for="album in visibleAlbums"
                :key="album.key"
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
                      {{ t('library.albumMeta', { tracks: album.files.length }) }}
                    </p>
                  </div>
                </article>
              </li>
            </ul>

            <ul
              v-else-if="browseView === 'genres'"
              class="player-browse-grid"
            >
              <li v-for="genre in filteredGenres" :key="genre.name">
                <article
                  class="player-browse-card"
                  role="button"
                  tabindex="0"
                  @click="openGenre(genre.name)"
                  @keydown.enter="openGenre(genre.name)"
                  @keydown.space.prevent="openGenre(genre.name)"
                >
                  <div class="player-browse-card-cover">
                    <GenreCover :name="genre.name" :files="genre.coverFiles" />
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
                      {{ t('player.genreMeta', { count: genre.files.length }) }}
                    </p>
                  </div>
                </article>
              </li>
            </ul>

            <ul
              v-else-if="browseView === 'tracks' && visibleTrackItems.length > 0"
              class="player-browse-grid"
            >
              <li
                v-for="item in visibleTrackItems"
                :key="item.file"
              >
                <button
                  type="button"
                  class="player-browse-card"
                  :class="{ 'player-browse-card-active': isCurrentFile(item.file) }"
                  @click="playFiles(visibleTrackFiles, item.file)"
                >
                  <div
                    class="player-browse-card-cover"
                    :class="{ 'ring-2 ring-primary/50': isCurrentFile(item.file) }"
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
                      v-if="isCurrentFile(item.file) && player.isPlaying.value"
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

            <div
              v-else-if="libraryFilter"
              class="py-10 text-center"
            >
              <p class="text-sm text-base-content/50">
                {{ t('player.noFilterResults') }}
              </p>
            </div>

            <div v-else class="py-10 text-center">
              <p class="text-sm text-base-content/50">{{ t('player.empty') }}</p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Icon } from '@iconify/vue'
import Navbar from '/src/components/Navbar.vue'
import CoverImage from '/src/components/CoverImage.vue'
import GenreCover from '/src/components/GenreCover.vue'
import API from '/src/model/api'
import {
  groupAlbums,
  groupArtists,
  groupGenres,
  matchesLibraryFilter,
  normalizeLibraryItem,
} from '/src/model/library'
import { usePlayer, formatTime, trackInfoFromFile } from '/src/model/player'
import { useMobileSearch } from '/src/model/mobileSearch'
import { useI18n } from '/src/i18n'

const { t } = useI18n()
const player = usePlayer()
const mobileSearch = useMobileSearch()
const libraryFilter = mobileSearch.libraryFilter

const files = ref([])
const libraryItems = ref([])
const loading = ref(false)
const browseMode = ref('artists')
const selectedArtistName = ref('')
const selectedAlbumKey = ref('')
const selectedGenreName = ref('')
const progressBar = ref(null)
let dragging = false
let genreRefreshTimers = []

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
  const q = libraryFilter.value
  if (!q) return artists.value
  return artists.value.filter((artist) =>
    artist.files.some((file) => {
      const item = libraryItems.value.find((entry) => entry.file === file)
      return item ? matchesLibraryFilter(item, q) : false
    })
  )
})

const visibleAlbums = computed(() => {
  const source =
    browseView.value === 'artist-albums'
      ? artistAlbums.value
      : albums.value
  const q = libraryFilter.value
  if (!q) return source
  return source.filter((album) =>
    album.files.some((file) => {
      const item = libraryItems.value.find((entry) => entry.file === file)
      return item ? matchesLibraryFilter(item, q) : false
    })
  )
})

const filteredGenres = computed(() => {
  const q = libraryFilter.value
  const source = q
    ? genres.value.filter((genre) =>
        genre.files.some((file) => {
          const item = libraryItems.value.find((entry) => entry.file === file)
          return item ? matchesLibraryFilter(item, q) : false
        })
      )
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
      const genre =
        item.browse_genre || item.genre || unknownGenreLabel.value
      return genre === selectedGenreName.value
    })
  }

  const q = libraryFilter.value
  if (q) {
    items = items.filter((item) => matchesLibraryFilter(item, q))
  }

  return items
})

const visibleTrackFiles = computed(() =>
  visibleTrackItems.value.map((item) => item.file)
)

const browsePlayFiles = computed(() => {
  if (browseView.value !== 'tracks') return []
  return visibleTrackFiles.value
})

const canBrowseBack = computed(
  () =>
    Boolean(
      selectedAlbumKey.value ||
        selectedArtistName.value ||
        selectedGenreName.value
    )
)

const browseHeading = computed(() => {
  if (selectedAlbum.value) return selectedAlbum.value.name
  if (selectedGenreName.value) return selectedGenreName.value
  if (selectedArtistName.value) return selectedArtistName.value
  return t('player.browse')
})

const browseSubtitle = computed(() => {
  if (selectedAlbum.value) return selectedAlbum.value.artist
  if (selectedGenreName.value) {
    return t('player.genreMeta', {
      count: visibleTrackItems.value.length,
    })
  }
  if (selectedArtistName.value && artistAlbums.value.length > 0) {
    return t('library.artistMeta', {
      tracks: selectedArtist.value?.files.length || 0,
      albums: artistAlbums.value.length,
    })
  }
  return ''
})

const browseBackLabel = computed(() => {
  if (selectedAlbumKey.value) return selectedArtistName.value || t('library.albums')
  if (selectedGenreName.value) return t('player.genres')
  return t('library.backToArtists')
})

const browseCountText = computed(() => {
  if (browseView.value === 'artists') {
    return t('player.artistBrowseCount', {
      count: filteredArtists.value.length,
    })
  }
  if (browseView.value === 'albums' || browseView.value === 'artist-albums') {
    return t('player.albumBrowseCount', {
      count: visibleAlbums.value.length,
    })
  }
  if (browseView.value === 'genres') {
    return t('player.genreBrowseCount', {
      count: filteredGenres.value.length,
    })
  }
  const count = visibleTrackItems.value.length
  return count === 1
    ? t('player.countOne', { count })
    : t('player.countMany', { count })
})

const currentCoverSources = computed(() => {
  const file = player.currentTrack.value?.file || ''
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

function applyLibraryItems(items) {
  const options = libraryGroupOptions.value
  libraryItems.value = items.map((item) => normalizeLibraryItem(item, options))
  files.value = libraryItems.value.map((item) => item.file)
}

function libraryItemsUnchanged(nextItems) {
  const current = libraryItems.value
  if (nextItems.length !== current.length) return false
  return nextItems.every((item, index) => {
    const existing = current[index]
    return (
      existing?.file === item.file &&
      existing?.title === item.title &&
      existing?.artist === item.artist &&
      existing?.album === item.album &&
      existing?.genre === item.genre &&
      existing?.browse_genre === item.browse_genre
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
  try {
    const res = await API.getLibraryFiles()
    const items = Array.isArray(res.data) ? res.data : []
    if (items.length > 0 && !libraryItemsUnchanged(items)) {
      applyLibraryItems(items)
      scheduleGenreRefresh(items)
    }
  } catch {
    // Ignore background refresh failures.
  }
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

async function load() {
  loading.value = true
  try {
    const listRes = await API.listDownloads()
    const paths = listRes.data || []
    files.value = paths
    if (paths.length > 0) {
      applyLibraryItems(fallbackLibraryItems(paths))
      if (player.playlist.value.length === 0) {
        player.setPlaylist(paths)
      }
    } else {
      libraryItems.value = []
    }
  } catch {
    try {
      const res = await API.listDownloads()
      const paths = res.data || []
      applyLibraryItems(fallbackLibraryItems(paths))
      files.value = paths
      if (player.playlist.value.length === 0 && files.value.length > 0) {
        player.setPlaylist(files.value)
      }
    } catch {
      files.value = []
      libraryItems.value = []
    }
  } finally {
    loading.value = false
  }
  refreshLibraryMetadata()
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

function isCurrentFile(file) {
  return player.currentTrack.value?.file === file
}

function clearLibraryFilter() {
  mobileSearch.clearLibraryFilter()
}

const trackTitle = computed(() => {
  const c = player.currentTrack.value
  if (c && c.title) return c.title
  return t('player.empty')
})

const trackArtist = computed(() => {
  const c = player.currentTrack.value
  if (c && c.artist) return c.artist
  if (c) return t('common.unknownArtist')
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
  const el = progressBar.value
  if (!el) return 0
  const rect = el.getBoundingClientRect()
  const x = (e.clientX || 0) - rect.left
  return Math.max(0, Math.min(1, x / rect.width))
}

function onSeekClick(e) {
  player.seekRatio(ratioFromEvent(e))
}

function onSeekStart(e) {
  dragging = true
  player.seekRatio(ratioFromEvent(e))
  window.addEventListener('pointermove', onSeekDrag)
  window.addEventListener('pointerup', onSeekEnd, { once: true })
}

function onSeekDrag(e) {
  if (!dragging) return
  player.seekRatio(ratioFromEvent(e))
}

function onSeekEnd() {
  dragging = false
  window.removeEventListener('pointermove', onSeekDrag)
}

onMounted(() => {
  window.scroll(0, 0)
  load()
})

onUnmounted(() => {
  clearGenreRefreshTimers()
  window.removeEventListener('pointermove', onSeekDrag)
})
</script>

<style scoped>
@media (max-width: 1023px) {
  .player-view {
    display: flex;
    flex-direction: column;
    min-height: 0;
    height: auto;
    overflow: visible;
  }

  .player-page {
    min-height: 0;
    flex: 1 1 auto;
  }

  .player-shell {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    min-height: auto;
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
    flex: 1 1 auto;
    min-height: min(62vh, 38rem);
    overflow: hidden;
  }

  .player-browse-body {
    min-height: min(52vh, 32rem);
    -webkit-overflow-scrolling: touch;
  }
}

@media (min-width: 1024px) {
  .player-shell {
    display: grid;
    grid-template-columns: 1fr 360px;
    gap: 1.5rem;
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
  padding: 0.625rem 0;
  cursor: pointer;
  touch-action: none;
}

.player-progress-track {
  position: relative;
  height: 4px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
}

[data-theme='downtify-light'] .player-progress-track {
  background: rgba(0, 0, 0, 0.1);
}

.player-progress-fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: 9999px;
  background: #1ad05c;
  transition: width 150ms ease;
}

.player-progress-thumb {
  position: absolute;
  top: 50%;
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
  transform: translateY(-50%);
  transition: left 150ms ease;
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
  @apply mb-3 w-full max-w-full grid grid-cols-2 gap-1 rounded-2xl border border-white/10 bg-base-100/75 p-1 sm:mx-auto sm:mb-4 sm:flex sm:w-max sm:max-w-full sm:rounded-full;
}

.player-browse-tabs .metadata-tab-btn {
  @apply inline-flex w-full items-center justify-center gap-1 whitespace-normal rounded-xl px-2 py-2.5 text-center text-[11px] font-medium leading-tight transition-colors sm:w-auto sm:gap-0 sm:whitespace-nowrap sm:rounded-full sm:px-4 sm:py-2 sm:text-sm sm:leading-normal;
}

.player-browse-body {
  @apply min-h-0;
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
