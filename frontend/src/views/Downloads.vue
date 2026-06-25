<template>
  <div class="library-view">
    <Navbar />

    <div class="library-page">
      <div class="library-chrome">
        <div
          v-if="error"
          class="surface mb-3 flex items-center gap-3 rounded-2xl p-4 text-sm text-error"
        >
          <Icon
            icon="clarity:exclamation-circle-line"
            class="h-5 w-5 shrink-0"
          />
          <span>{{ error }}</span>
        </div>

        <div v-if="files.length > 0" class="library-chrome-tools space-y-2">
          <form class="library-search" @submit.prevent="submitLibrarySearch">
            <SearchField
              root-class="w-full flex-1"
              v-model="librarySearchQuery"
              :placeholder="t('library.searchPlaceholder')"
              :aria-label="t('library.searchPlaceholder')"
              :submit-disabled="!librarySearchActive"
              @clear="clearLibrarySearch"
              @submit="submitLibrarySearch"
            />
          </form>

          <div class="library-tabs">
            <button
              class="library-tab-btn"
              :class="
                viewMode === 'artists'
                  ? 'library-tab-btn-active'
                  : 'library-tab-btn-inactive'
              "
              @click="showArtists"
            >
              {{ t('library.artists') }}
            </button>
            <button
              class="library-tab-btn"
              :class="
                viewMode === 'albums'
                  ? 'library-tab-btn-active'
                  : 'library-tab-btn-inactive'
              "
              @click="showAlbums"
            >
              {{ t('library.albums') }}
            </button>
            <button
              class="library-tab-btn"
              :class="
                viewMode === 'tracks'
                  ? 'library-tab-btn-active'
                  : 'library-tab-btn-inactive'
              "
              @click="showTracks"
            >
              {{ t('library.tracks') }}
            </button>
            <button
              class="library-tab-btn"
              :class="
                viewMode === 'genres'
                  ? 'library-tab-btn-active'
                  : 'library-tab-btn-inactive'
              "
              @click="showGenres"
            >
              {{ t('library.genres') }}
            </button>
          </div>
        </div>

        <div
          v-if="viewMode === 'artists' && selectedArtist && !selectedAlbum"
          class="library-drill-header"
        >
          <div class="library-drill-toolbar">
            <button class="library-drill-back" @click="closeArtist">
              <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-[-90deg]" />
              {{ t('library.backToArtists') }}
            </button>
            <div class="library-drill-actions">
              <LibraryArtistMonitor :artist-name="selectedArtist.name" />
            </div>
          </div>
          <div class="library-drill-main">
            <h2 class="library-drill-title">
              {{ selectedArtist.name }}
            </h2>
            <p class="library-drill-meta">
              {{
                t('library.artistMeta', {
                  tracks: selectedArtist.files.length,
                  albums: selectedArtist.albumCount,
                })
              }}
            </p>
          </div>
        </div>

        <div
          v-if="viewMode === 'genres' && selectedGenreName"
          class="library-drill-header"
        >
          <button class="library-drill-back" @click="closeGenre">
            <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-[-90deg]" />
            {{ t('library.backToGenres') }}
          </button>
          <div class="library-drill-main">
            <h2 class="library-drill-title">
              {{ selectedGenreName }}
            </h2>
            <p class="library-drill-meta">
              {{
                t('library.genreMeta', {
                  tracks: selectedGenreFiles.length,
                })
              }}
            </p>
          </div>
        </div>

        <div v-if="selectedAlbum" class="library-drill-header">
          <button class="library-drill-back" @click="closeAlbum">
            <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-[-90deg]" />
            {{
              selectedArtist ? t('library.backToAlbums') : t('library.albums')
            }}
          </button>
          <div class="library-drill-main">
            <h2 class="library-drill-title">
              {{ selectedAlbum.name }}
            </h2>
            <p class="library-drill-meta">
              {{ albumArtistsLabel(selectedAlbum) }} -
              {{
                t('library.albumMeta', { tracks: selectedAlbum.files.length })
              }}
            </p>
          </div>
        </div>
      </div>

      <div class="library-browse-slot">
        <div
          v-if="loading && files.length === 0"
          class="panel-glow-shell panel-glow-shell-grow surface min-h-0 rounded-3xl"
        >
          <div class="library-browse panel-glow-inner p-3 sm:p-5">
            <div class="library-browse-body">
              <div class="library-browse-grid">
                <div
                  v-for="n in 6"
                  :key="n"
                  class="skeleton aspect-square rounded-2xl"
                />
              </div>
            </div>
          </div>
        </div>

        <div
          v-else-if="files.length === 0"
          class="panel-glow-shell panel-glow-shell-grow surface min-h-0 rounded-3xl"
        >
          <div
            class="library-browse panel-glow-inner flex flex-col p-12 text-center"
          >
            <div
              class="library-browse-body flex flex-col items-center justify-center"
            >
              <Icon
                icon="clarity:library-line"
                class="mb-4 h-12 w-12 text-base-content/20"
              />
              <p class="text-sm text-base-content/50">
                {{ t('library.empty') }}
              </p>
              <p class="mt-1 text-xs text-base-content/40">
                {{ t('library.emptyHint') }}
              </p>
            </div>
          </div>
        </div>

        <div
          v-else
          class="panel-glow-shell panel-glow-shell-grow surface min-h-0 rounded-3xl"
        >
          <div class="library-browse panel-glow-inner p-3 sm:p-5">
            <div ref="browseBodyRef" class="library-browse-body">
              <div v-if="showLibraryNoSearchResults">
                <div
                  v-if="librarySearchIsUrl"
                  class="flex flex-col items-center gap-4 px-4 py-10 text-center"
                >
                  <Icon
                    icon="clarity:link-line"
                    class="h-10 w-10 text-base-content/20"
                  />
                  <div>
                    <p class="text-sm font-semibold">
                      {{ t('library.notInLibrary') }}
                    </p>
                    <p class="mt-1 text-xs text-base-content/50">
                      {{ t('library.downloadFromLinkHint') }}
                    </p>
                  </div>
                  <button
                    type="button"
                    class="btn btn-primary rounded-full"
                    @click="downloadFromLibrarySearchUrl"
                  >
                    <Icon icon="clarity:download-line" class="h-4 w-4" />
                    {{ t('library.downloadFromLink') }}
                  </button>
                </div>
                <template v-else>
                  <div
                    class="mb-1 flex flex-col items-center px-4 py-6 text-center"
                  >
                    <Icon
                      icon="clarity:search-line"
                      class="mb-3 h-10 w-10 text-base-content/20"
                    />
                    <p class="text-sm text-base-content/50">
                      {{ t('library.noSearchResults') }}
                    </p>
                  </div>
                  <ServerConnectionPrompt v-if="needsServerConnection()" />
                  <LibraryDownloadOffers
                    v-else
                    :items="onlineResults"
                    :loading="onlineLoading"
                    :error="onlineError"
                    @download="queueOnlineDownload"
                  />
                </template>
              </div>

              <ul
                v-else-if="viewMode === 'artists' && !selectedArtist"
                class="library-browse-grid"
              >
                <li
                  v-for="artist in filteredArtists"
                  :key="artist.name"
                  class="browse-tile-shell"
                >
                  <article
                    class="library-browse-card"
                    role="button"
                    tabindex="0"
                    @click="openArtist(artist.name)"
                    @keydown.enter="openArtist(artist.name)"
                    @keydown.space.prevent="openArtist(artist.name)"
                  >
                    <div class="library-browse-card-cover">
                      <CoverImage
                        v-if="
                          artistCoverProps(artist).src ||
                          artistCoverProps(artist).fallbacks.length
                        "
                        :key="`artist:${artist.name}`"
                        :src="artistCoverProps(artist).src"
                        :fallbacks="artistCoverProps(artist).fallbacks"
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
                        class="library-browse-card-play"
                        :title="t('library.playArtist')"
                        @click.stop="playArtist(artist)"
                      >
                        <Icon icon="clarity:play-line" class="h-4 w-4" />
                      </button>
                      <LibraryArtistMonitorBadge :artist-name="artist.name" />
                    </div>
                    <div class="library-browse-card-body">
                      <p class="library-browse-card-title">{{ artist.name }}</p>
                      <p class="library-browse-card-sub">
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
                  (viewMode === 'albums' ||
                    (viewMode === 'artists' && selectedArtist)) &&
                  !selectedAlbum
                "
                class="library-browse-grid"
              >
                <li
                  v-for="album in filteredVisibleAlbums"
                  :key="album.key"
                  class="browse-tile-shell"
                >
                  <article
                    class="library-browse-card"
                    role="button"
                    tabindex="0"
                    @click="openAlbum(album)"
                    @keydown.enter="openAlbum(album)"
                    @keydown.space.prevent="openAlbum(album)"
                  >
                    <div class="library-browse-card-cover">
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
                        class="library-browse-card-play"
                        :title="t('library.playAlbum')"
                        @click.stop="playAlbum(album)"
                      >
                        <Icon icon="clarity:play-line" class="h-4 w-4" />
                      </button>
                    </div>
                    <div class="library-browse-card-body">
                      <p class="library-browse-card-title">{{ album.name }}</p>
                      <p class="library-browse-card-sub">
                        {{ albumArtistsLabel(album) }}
                      </p>
                      <p class="library-browse-card-meta">
                        {{
                          t('library.albumMeta', { tracks: album.files.length })
                        }}
                      </p>
                    </div>
                  </article>
                </li>
              </ul>

              <ul
                v-else-if="viewMode === 'genres' && !selectedGenreName"
                class="library-browse-grid"
              >
                <li
                  v-for="genre in filteredGenres"
                  :key="genre.name"
                  class="browse-tile-shell"
                >
                  <article
                    class="library-browse-card"
                    role="button"
                    tabindex="0"
                    @click="openGenre(genre.name)"
                    @keydown.enter="openGenre(genre.name)"
                    @keydown.space.prevent="openGenre(genre.name)"
                  >
                    <div class="library-browse-card-cover">
                      <GenreCover
                        :name="genre.name"
                        :files="genre.coverFiles"
                      />
                      <button
                        type="button"
                        class="library-browse-card-play"
                        :title="t('library.playGenre')"
                        @click.stop="playGenre(genre)"
                      >
                        <Icon icon="clarity:play-line" class="h-4 w-4" />
                      </button>
                    </div>
                    <div class="library-browse-card-body">
                      <p class="library-browse-card-title">{{ genre.name }}</p>
                      <p
                        v-if="genre.subgenres?.length"
                        class="library-browse-card-sub truncate"
                      >
                        {{ genre.subgenres.slice(0, 3).join(' · ') }}
                      </p>
                      <p class="library-browse-card-meta">
                        {{
                          t('library.genreMeta', { tracks: genre.files.length })
                        }}
                      </p>
                    </div>
                  </article>
                </li>
              </ul>

              <ul
                v-else-if="
                  viewMode === 'tracks' ||
                  selectedAlbum ||
                  (selectedArtist && selectedArtistAlbums.length === 0) ||
                  selectedGenreName
                "
                class="library-track-list space-y-2"
              >
                <li
                  v-for="file in filteredVisibleFiles"
                  :key="file"
                  class="browse-tile-shell"
                >
                  <div
                    class="library-track-row rounded-2xl border border-primary/20 bg-base-100/90 p-3 sm:p-4 flex items-center gap-3"
                  >
                    <!-- Cover thumb -->
                    <div
                      class="relative h-11 w-11 shrink-0 overflow-hidden rounded-xl bg-base-200/80"
                    >
                      <CoverImage
                        :key="file"
                        :src="coverSourcesFor(file).src"
                        :fallbacks="coverSourcesFor(file).fallbacks"
                        :alt="file"
                        img-class="absolute inset-0 h-full w-full object-cover"
                      >
                        <template #fallback>
                          <div
                            class="flex h-full w-full items-center justify-center text-base-content/35"
                          >
                            <Icon
                              icon="clarity:music-note-line"
                              class="h-5 w-5"
                            />
                          </div>
                        </template>
                      </CoverImage>
                    </div>

                    <!-- Filename -->
                    <div class="flex-1 min-w-0">
                      <span class="text-sm font-medium truncate block">{{
                        displayName(file)
                      }}</span>
                      <span class="text-xs text-base-content/40">
                        <span
                          v-if="folderOf(file)"
                          class="mr-2 text-primary/70"
                        >
                          <Icon
                            icon="clarity:folder-line"
                            class="inline h-3 w-3 mr-0.5 align-text-top"
                          />{{ folderOf(file) }}
                        </span>
                        {{ formatExt(file) }}
                      </span>
                    </div>

                    <!-- Actions -->
                    <div class="flex items-center gap-1 shrink-0">
                      <button
                        class="icon-btn text-primary hover:bg-primary/10"
                        @click="playFile(file)"
                        :title="t('library.play')"
                      >
                        <Icon icon="clarity:play-line" class="h-4 w-4" />
                      </button>
                      <template v-if="showTrackFileActions">
                        <a
                          class="icon-btn"
                          :href="API.downloadFileURL(file)"
                          download
                          :title="t('library.downloadToDevice')"
                        >
                          <Icon icon="clarity:download-line" class="h-4 w-4" />
                        </a>
                        <button
                          class="icon-btn text-error/70 hover:text-error hover:bg-error/10"
                          :disabled="deleting[file] === true"
                          @click="onDelete(file)"
                          :title="t('library.deleteFile')"
                        >
                          <span
                            v-if="deleting[file] === true"
                            class="loading loading-spinner loading-xs"
                          />
                          <Icon
                            v-else
                            icon="clarity:trash-line"
                            class="h-4 w-4"
                          />
                        </button>
                      </template>
                    </div>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ref,
  computed,
  watch,
  nextTick,
  onMounted,
  onActivated,
  onDeactivated,
  onUnmounted,
} from 'vue'
import { Icon } from '@iconify/vue'
import { useRouter } from 'vue-router'
import Navbar from '/src/components/Navbar.vue'
import CoverImage from '/src/components/CoverImage.vue'
import GenreCover from '/src/components/GenreCover.vue'
import LibraryDownloadOffers from '/src/components/LibraryDownloadOffers.vue'
import LibraryArtistMonitor from '/src/components/LibraryArtistMonitor.vue'
import LibraryArtistMonitorBadge from '/src/components/LibraryArtistMonitorBadge.vue'
import SearchField from '/src/components/SearchField.vue'
import ServerConnectionPrompt from '/src/components/ServerConnectionPrompt.vue'
import API from '/src/model/api'
import { beginAppLoading, endAppLoading } from '/src/model/appLoading'
import { useDownloadManager, scanDeviceLibraryPath } from '/src/model/download'
import {
  albumArtistsLabel,
  albumKey,
  displayNameFromFile,
  groupAlbums,
  groupArtists,
  groupGenres,
  itemMap,
  libraryItemsEqual,
  libraryGenreName,
  matchesLibraryAlbumEntry,
  matchesLibraryArtistName,
  matchesLibraryField,
  matchesLibraryGenreName,
  matchesLibraryTrackItem,
  normalizeLibraryItem,
  pathParts,
} from '/src/model/library'
import {
  fetchLibraryItems,
  getInitialLibrarySnapshot,
  onLibraryChanged,
  resetLibraryPrefetch,
} from '/src/model/librarySession'
import { buildApiBaseUrl, getServerConfig } from '/src/model/serverConnection'
import { useI18n } from '/src/i18n'
import { usePlayer } from '/src/model/player'
import { consumeLibraryNavigation } from '/src/model/libraryNavigation'
import { useLibraryRefresh } from '/src/model/libraryRefresh'
import { useLibraryOnlineSearch } from '/src/model/libraryOnlineSearch'
import { useSearchManager } from '/src/model/search'
import { needsServerConnection } from '/src/model/serverConnection'
import { refreshMonitoredArtists } from '/src/model/monitoredArtists'
import { preloadCoverSourcesBatch } from '/src/model/imageLoader'

defineOptions({ name: 'List' })

const libraryServerKey = buildApiBaseUrl(getServerConfig())
const initialLibrarySnapshot = getInitialLibrarySnapshot(libraryServerKey)

const { t } = useI18n()
const player = usePlayer()
const router = useRouter()
const libraryRefresh = useLibraryRefresh()
const dm = useDownloadManager()
const sm = useSearchManager()

const libraryItems = ref(initialLibrarySnapshot.items)
const files = ref(initialLibrarySnapshot.paths)
const loading = ref(!initialLibrarySnapshot.ready)
const error = ref('')
const deleting = ref({})
const viewMode = ref('artists')
const selectedArtistName = ref('')
const selectedAlbumKey = ref('')
const selectedGenreName = ref('')
const librarySearchQuery = ref('')
const browseBodyRef = ref(null)
const browseScrollPositions = new Map()

function currentBrowseScrollKey() {
  if (selectedAlbumKey.value) {
    return `album:${selectedAlbumKey.value}`
  }
  if (selectedGenreName.value) {
    return `genre:${selectedGenreName.value}`
  }
  if (selectedArtistName.value) {
    return `artist:${selectedArtistName.value}`
  }
  return `tab:${viewMode.value}`
}

function saveBrowseScrollPosition() {
  const el = browseBodyRef.value
  if (!el) return
  browseScrollPositions.set(currentBrowseScrollKey(), el.scrollTop)
}

function restoreBrowseScrollPosition(key) {
  const top = browseScrollPositions.get(key) ?? 0
  const apply = () => {
    const el = browseBodyRef.value
    if (el) el.scrollTop = top
  }
  nextTick(() => {
    apply()
    requestAnimationFrame(apply)
  })
}

function resetBrowseScrollPosition() {
  nextTick(() => {
    const el = browseBodyRef.value
    if (el) el.scrollTop = 0
  })
}

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

const selectedArtist = computed(() =>
  artists.value.find((artist) => artist.name === selectedArtistName.value)
)

const selectedArtistAlbums = computed(() => {
  if (!selectedArtist.value) return []
  return albums.value.filter(
    (album) => album.artist === selectedArtist.value.name
  )
})

const visibleAlbums = computed(() =>
  selectedArtist.value ? selectedArtistAlbums.value : albums.value
)

const selectedAlbum = computed(() =>
  visibleAlbums.value.find((album) => album.key === selectedAlbumKey.value)
)

const selectedGenreFiles = computed(() => {
  if (!selectedGenreName.value) return []
  const unknown = unknownGenreLabel.value
  return libraryItems.value
    .filter(
      (item) =>
        libraryGenreName(item, unknown, libraryGroupOptions.value) ===
        selectedGenreName.value
    )
    .map((item) => item.file)
})

const visibleFiles = computed(() => {
  if (selectedAlbum.value) return selectedAlbum.value.files
  if (selectedArtist.value) return selectedArtist.value.files
  if (selectedGenreName.value) return selectedGenreFiles.value
  if (viewMode.value === 'tracks') return files.value
  return files.value
})

const libraryItemByFile = computed(() => itemMap(libraryItems.value))

const librarySearchActive = computed(() =>
  Boolean(librarySearchQuery.value.trim())
)

const filteredArtists = computed(() => {
  const q = librarySearchQuery.value
  if (!librarySearchActive.value) return artists.value
  return artists.value.filter((artist) =>
    matchesLibraryArtistName(artist.name, q)
  )
})

const filteredVisibleAlbums = computed(() => {
  const q = librarySearchQuery.value
  const source = visibleAlbums.value
  if (!librarySearchActive.value) return source
  return source.filter((album) => matchesLibraryAlbumEntry(album, q))
})

const filteredGenres = computed(() => {
  const q = librarySearchQuery.value
  const source = genres.value
  const filtered = librarySearchActive.value
    ? source.filter((genre) => matchesLibraryGenreName(genre.name, q))
    : source
  const unknown = unknownGenreLabel.value
  const tagged = filtered.filter((genre) => genre.name !== unknown)
  return tagged.length > 0 ? tagged : filtered
})

const filteredVisibleFiles = computed(() => {
  const q = librarySearchQuery.value
  if (!librarySearchActive.value) return visibleFiles.value
  return visibleFiles.value.filter((file) => {
    const item = libraryItemByFile.value.get(file)
    if (item) return matchesLibraryTrackItem(item, q)
    return matchesLibraryField(displayNameFromFile(file), q)
  })
})

const showLibraryNoSearchResults = computed(() => {
  if (!librarySearchActive.value) return false
  if (viewMode.value === 'artists' && !selectedArtist.value) {
    return filteredArtists.value.length === 0
  }
  if (
    (viewMode.value === 'albums' ||
      (viewMode.value === 'artists' && selectedArtist.value)) &&
    !selectedAlbum.value
  ) {
    return filteredVisibleAlbums.value.length === 0
  }
  if (viewMode.value === 'genres' && !selectedGenreName.value) {
    return filteredGenres.value.length === 0
  }
  return filteredVisibleFiles.value.length === 0
})

const libraryOnlineViewMode = computed(() => {
  if (selectedAlbum.value) return 'tracks'
  if (selectedGenreName.value) return 'tracks'
  if (viewMode.value === 'artists' && selectedArtist.value) return 'albums'
  return viewMode.value
})

const showTrackFileActions = computed(
  () => viewMode.value !== 'tracks' && !selectedAlbum.value
)

const librarySearchIsUrl = computed(() =>
  sm.isValidURL(librarySearchQuery.value.trim())
)

const libraryOnlineSearchEnabled = computed(
  () =>
    librarySearchActive.value &&
    showLibraryNoSearchResults.value &&
    !needsServerConnection() &&
    !librarySearchIsUrl.value
)

const {
  results: onlineResults,
  loading: onlineLoading,
  error: onlineError,
} = useLibraryOnlineSearch(
  librarySearchQuery,
  libraryOnlineViewMode,
  libraryOnlineSearchEnabled
)

watch(selectedArtist, (artist) => {
  if (selectedArtistName.value && !artist) {
    selectedArtistName.value = ''
  }
})

watch(selectedAlbum, (album) => {
  if (selectedAlbumKey.value && !album) {
    selectedAlbumKey.value = ''
  }
})

function coverSourcesFor(file) {
  return API.coverSourcesForFile(file)
}

function artistCoverFor(artist) {
  return artistCoverMap.value.get(artist?.name) || API.coverSourcesForArtist('')
}

function artistCoverProps(artist) {
  const sources = artistCoverFor(artist)
  return {
    src: sources.src,
    fallbacks: sources.fallbacks,
  }
}

function warmVisibleArtistCovers(artistList = []) {
  const entries = artistList
    .slice(0, 100)
    .map((artist) => artistCoverFor(artist))
    .filter((entry) => entry.src || entry.fallbacks?.length)
  preloadCoverSourcesBatch(entries, { limit: 100, concurrency: 8 })
}

function warmVisibleAlbumCovers(albumList = []) {
  const entries = albumList
    .slice(0, 100)
    .map((album) => coverSourcesFor(album.coverFile))
    .filter((entry) => entry.src || entry.fallbacks?.length)
  preloadCoverSourcesBatch(entries, { limit: 100, concurrency: 8 })
}

function warmVisibleTrackCovers(trackList = []) {
  const entries = trackList
    .slice(0, 100)
    .map((file) => coverSourcesFor(file))
    .filter((entry) => entry.src || entry.fallbacks?.length)
  preloadCoverSourcesBatch(entries, { limit: 100, concurrency: 8 })
}

function warmVisibleCoversForCurrentView() {
  if (viewMode.value === 'artists' && !selectedArtist.value) {
    warmVisibleArtistCovers(filteredArtists.value)
    return
  }

  const inAlbumBrowse =
    viewMode.value === 'albums' ||
    (viewMode.value === 'artists' && selectedArtist.value)
  if (inAlbumBrowse && !selectedAlbum.value) {
    warmVisibleAlbumCovers(filteredVisibleAlbums.value)
    return
  }

  if (
    viewMode.value === 'tracks' ||
    selectedAlbum.value ||
    selectedGenreName.value
  ) {
    warmVisibleTrackCovers(filteredVisibleFiles.value)
  }
}

watch(
  () =>
    viewMode.value === 'artists' && !selectedArtist.value
      ? filteredArtists.value.map((artist) => artist.name).join('\0')
      : '',
  () => {
    if (viewMode.value !== 'artists' || selectedArtist.value) return
    warmVisibleArtistCovers(filteredArtists.value)
  },
  { immediate: true }
)

watch(
  () => {
    const inAlbumBrowse =
      (viewMode.value === 'albums' ||
        (viewMode.value === 'artists' && selectedArtist.value)) &&
      !selectedAlbum.value
    return inAlbumBrowse
      ? filteredVisibleAlbums.value.map((album) => albumKey(album)).join('\0')
      : ''
  },
  () => {
    if (selectedAlbum.value) return
    const inAlbumBrowse =
      viewMode.value === 'albums' ||
      (viewMode.value === 'artists' && selectedArtist.value)
    if (!inAlbumBrowse) return
    warmVisibleAlbumCovers(filteredVisibleAlbums.value)
  },
  { immediate: true }
)

watch(
  () =>
    viewMode.value === 'tracks' ||
    selectedAlbum.value ||
    selectedGenreName.value
      ? filteredVisibleFiles.value.join('\0')
      : '',
  () => {
    if (
      viewMode.value !== 'tracks' &&
      !selectedAlbum.value &&
      !selectedGenreName.value
    ) {
      return
    }
    warmVisibleTrackCovers(filteredVisibleFiles.value)
  },
  { immediate: true }
)

function applyLibraryData(items) {
  const options = libraryGroupOptions.value
  const normalized = items.map((item) => normalizeLibraryItem(item, options))
  if (libraryItemsEqual(libraryItems.value, normalized)) return
  libraryItems.value = normalized
  files.value = libraryItems.value.map((item) => item.file)
  API.warmLibraryCovers(libraryItems.value)
  warmVisibleCoversForCurrentView()
  scheduleGenreRefresh(libraryItems.value)
  applyPendingLibraryNavigation()
}

function applyPendingLibraryNavigation() {
  const intent = consumeLibraryNavigation()
  if (!intent) return
  viewMode.value = intent.browseMode || 'artists'
  selectedArtistName.value = intent.selectedArtistName || ''
  selectedAlbumKey.value = intent.selectedAlbumKey || ''
  selectedGenreName.value = intent.selectedGenreName || ''
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

function scheduleGenreRefresh(items) {
  clearGenreRefreshTimers()
  if (countUnknownGenres(items) === 0) return

  for (const delay of [3000, 10000, 30000, 90000, 300000]) {
    genreRefreshTimers.push(
      setTimeout(() => {
        void refresh({ background: true })
      }, delay)
    )
  }
}

function pathsToLibraryItems(paths) {
  const options = libraryGroupOptions.value
  return (paths || []).map((file) => normalizeLibraryItem({ file }, options))
}

function hydrateLibraryFromSession() {
  const snapshot = getInitialLibrarySnapshot(libraryServerKey)
  if (!snapshot.ready) return false
  libraryItems.value = snapshot.items.map((item) =>
    normalizeLibraryItem(item, libraryGroupOptions.value)
  )
  files.value = snapshot.paths
  API.warmLibraryCovers(libraryItems.value)
  return true
}

async function refreshFromHeader() {
  libraryRefresh.setFailed(false)
  libraryRefresh.setLoading(true)
  error.value = ''
  try {
    resetLibraryPrefetch()
    const items = await fetchLibraryItems(
      () => API.getLibraryFiles().then((res) => res.data || []),
      { preferPrefetch: false }
    )
    if (items.length > 0) {
      applyLibraryData(items)
      return
    }

    const res = await API.listDownloads()
    applyLibraryData(pathsToLibraryItems(res.data || []))
  } catch {
    libraryRefresh.setFailed(true)
    error.value = t('library.failedLoad')
  } finally {
    libraryRefresh.setLoading(false)
  }
}

async function refresh({ background = false, force = false } = {}) {
  const hadCache = files.value.length > 0 || hydrateLibraryFromSession()
  if (!background) {
    loading.value = !hadCache
    if (!hadCache) beginAppLoading()
  }
  error.value = ''
  try {
    if (background) {
      const items = await API.refreshLibraryInBackground(force)
      if (items.length) applyLibraryData(items)
      return
    }

    const items = await fetchLibraryItems(
      () => API.getLibraryFiles().then((res) => res.data || []),
      { preferPrefetch: true }
    )
    if (items.length > 0) {
      applyLibraryData(items)
      return
    }

    const res = await API.listDownloads()
    applyLibraryData(pathsToLibraryItems(res.data || []))
  } catch {
    if (!hadCache) {
      error.value = t('library.failedLoad')
    }
  } finally {
    loading.value = false
    if (!background && !hadCache) endAppLoading()
  }
}

async function onDelete(file) {
  if (!confirm(t('library.deletePrompt', { file }))) return
  deleting.value = { ...deleting.value, [file]: true }
  try {
    await API.deleteDownload(file)
    scanDeviceLibraryPath(file)
    files.value = files.value.filter((f) => f !== file)
    libraryItems.value = libraryItems.value.filter((item) => item.file !== file)
  } catch {
    error.value = t('library.failedDelete', { file })
  } finally {
    deleting.value = { ...deleting.value, [file]: false }
  }
}

function formatExt(file) {
  const dot = file.lastIndexOf('.')
  return dot > 0 ? file.slice(dot + 1).toUpperCase() : ''
}

function displayName(file) {
  return displayNameFromFile(file)
}

function folderOf(file) {
  const parts = pathParts(file)
  if (parts.length <= 1) return ''
  return parts.slice(0, -1).join('/')
}

function switchLibraryTab(mode) {
  saveBrowseScrollPosition()
  viewMode.value = mode
  selectedArtistName.value = ''
  selectedAlbumKey.value = ''
  selectedGenreName.value = ''
  restoreBrowseScrollPosition(`tab:${mode}`)
}

function showArtists() {
  switchLibraryTab('artists')
}

function showAlbums() {
  switchLibraryTab('albums')
}

function showTracks() {
  switchLibraryTab('tracks')
}

function showGenres() {
  switchLibraryTab('genres')
}

function openArtist(name) {
  saveBrowseScrollPosition()
  selectedArtistName.value = name
  selectedAlbumKey.value = ''
  selectedGenreName.value = ''
  resetBrowseScrollPosition()
}

function closeArtist() {
  const restoreKey = `tab:${viewMode.value}`
  saveBrowseScrollPosition()
  selectedArtistName.value = ''
  selectedAlbumKey.value = ''
  restoreBrowseScrollPosition(restoreKey)
}

function openAlbum(album) {
  saveBrowseScrollPosition()
  selectedAlbumKey.value = album.key
  selectedGenreName.value = ''
  resetBrowseScrollPosition()
}

function closeAlbum() {
  const restoreKey = selectedArtistName.value
    ? `artist:${selectedArtistName.value}`
    : `tab:${viewMode.value}`
  saveBrowseScrollPosition()
  selectedAlbumKey.value = ''
  restoreBrowseScrollPosition(restoreKey)
}

function openGenre(name) {
  saveBrowseScrollPosition()
  selectedGenreName.value = name
  selectedArtistName.value = ''
  selectedAlbumKey.value = ''
  resetBrowseScrollPosition()
}

function closeGenre() {
  const restoreKey = 'tab:genres'
  saveBrowseScrollPosition()
  selectedGenreName.value = ''
  restoreBrowseScrollPosition(restoreKey)
}

function playFile(file) {
  saveBrowseScrollPosition()
  const playlist = visibleFiles.value
  player.setPlaylist(playlist, { startIndex: playlist.indexOf(file) })
  router.push({ name: 'Player' })
}

function playArtist(artist) {
  saveBrowseScrollPosition()
  player.setPlaylist(artist.files, { startIndex: 0 })
  router.push({ name: 'Player' })
}

function playAlbum(album) {
  saveBrowseScrollPosition()
  player.setPlaylist(album.files, { startIndex: 0 })
  router.push({ name: 'Player' })
}

function playGenre(genre) {
  saveBrowseScrollPosition()
  player.setPlaylist(genre.files, { startIndex: 0 })
  router.push({ name: 'Player' })
}

function clearLibrarySearch() {
  librarySearchQuery.value = ''
}

function submitLibrarySearch() {
  if (librarySearchIsUrl.value) {
    downloadFromLibrarySearchUrl()
  }
}

function downloadFromLibrarySearchUrl() {
  const url = librarySearchQuery.value.trim()
  if (!url || !sm.isValidURL(url)) return
  dm.fromURL(url)
  router.push({ name: 'Download' })
}

function queueOnlineDownload(song) {
  dm.queue(song)
}

let stopLibraryListener = null
let genreRefreshTimers = []

onMounted(() => {
  libraryRefresh.register(refreshFromHeader)
  if (libraryItems.value.length) {
    API.warmLibraryCovers(libraryItems.value)
    warmVisibleCoversForCurrentView()
  }
  void refreshMonitoredArtists()
  void refresh()
  stopLibraryListener = onLibraryChanged(() => {
    void refresh({ background: true, force: true })
  })
})

onActivated(() => {
  libraryRefresh.register(refreshFromHeader)
  restoreBrowseScrollPosition(currentBrowseScrollKey())
  if (files.value.length > 0) {
    warmVisibleCoversForCurrentView()
    void refresh({ background: true })
    return
  }
  void refresh()
})

onDeactivated(() => {
  saveBrowseScrollPosition()
  libraryRefresh.unregister()
})

onUnmounted(() => {
  stopLibraryListener?.()
  clearGenreRefreshTimers()
  libraryRefresh.unregister()
})
</script>

<style scoped>
.library-view {
  @apply flex min-h-0 flex-col overflow-hidden;
  height: calc(
    100dvh - var(--app-header-height) - var(--app-safe-top) -
      var(--app-bottom-nav-height) - var(--app-safe-bottom)
  );
  max-height: calc(
    100dvh - var(--app-header-height) - var(--app-safe-top) -
      var(--app-bottom-nav-height) - var(--app-safe-bottom)
  );
}

@media (min-width: 1024px) {
  .library-view {
    height: auto;
    max-height: none;
    overflow: visible;
  }

  .library-chrome {
    @apply sticky top-16 z-20 -mx-4 bg-base-100/90 px-4 pb-3 backdrop-blur-md sm:-mx-6 sm:px-6;
  }

  .library-browse-slot {
    flex: none;
  }

  .library-browse {
    flex: none;
    min-height: auto;
  }

  .library-browse-body {
    overflow: visible;
    max-height: none;
  }
}

.library-page {
  @apply mx-auto flex w-full max-w-4xl flex-1 flex-col gap-2 min-h-0 px-4 py-3 sm:px-6 lg:overflow-visible lg:py-8;
}

.library-chrome {
  @apply shrink-0 space-y-3;
}

.library-search {
  @apply flex w-full items-center;
}

.library-tabs {
  @apply flex w-full min-w-0 gap-1 rounded-full border border-white/10 bg-base-100/75 p-1;
}

.library-tab-btn {
  @apply min-w-0 flex-1 truncate rounded-full px-2 py-2 text-center text-xs font-medium transition-colors sm:px-3 sm:text-sm;
}

.library-tab-btn-active {
  @apply bg-primary text-primary-content shadow-glow-sm;
}

.library-tab-btn-inactive {
  @apply text-base-content/60 hover:text-base-content;
}

.library-drill-header {
  @apply flex flex-col items-stretch gap-3;
}

.library-drill-toolbar {
  @apply flex w-full flex-nowrap items-center justify-between gap-2;
}

.library-drill-back {
  @apply btn btn-sm inline-flex h-10 min-w-0 shrink items-center gap-1.5 rounded-full border-white/10 bg-base-100/85 px-3 hover:bg-base-100 sm:px-4;
}

.library-drill-main {
  @apply min-w-0 w-full;
}

.library-drill-title {
  @apply text-base font-semibold leading-snug sm:text-lg;
}

.library-drill-meta {
  @apply mt-0.5 text-xs text-base-content/50;
}

.library-drill-actions {
  @apply flex shrink-0 flex-nowrap items-center justify-end gap-2;
}

.library-drill-header :deep(.library-artist-monitor .btn) {
  @apply h-10 whitespace-nowrap px-3 sm:px-4;
}

.library-browse-slot {
  @apply flex min-h-0 flex-1 flex-col;
}

.library-browse {
  @apply flex min-h-0 flex-1 flex-col;
}

.library-browse-body {
  @apply min-h-0 flex-1 overflow-x-hidden overflow-y-auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.library-browse-body::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.library-browse-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

@media (min-width: 640px) {
  .library-browse-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .library-browse-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.library-browse-card {
  @apply flex h-full w-full cursor-pointer flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/5 text-left transition-colors hover:border-primary/25 hover:bg-white/[0.07] active:bg-white/10;
}

.library-track-row {
  @apply backdrop-blur-md;
}

.library-browse-card-cover {
  @apply relative aspect-square w-full shrink-0 overflow-hidden bg-primary/10;
}

.library-browse-card-play {
  @apply absolute bottom-2 right-2 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-content shadow-glow-sm transition-transform active:scale-95;
}

.library-browse-card-body {
  @apply p-2.5;
}

.library-browse-card-title {
  @apply truncate text-sm font-semibold leading-snug;
}

.library-browse-card-sub {
  @apply mt-0.5 line-clamp-2 text-[11px] leading-4 text-base-content/50;
}

.library-browse-card-meta {
  @apply mt-0.5 text-[11px] text-base-content/40;
}

.library-track-list {
  @apply min-w-0;
}
</style>
