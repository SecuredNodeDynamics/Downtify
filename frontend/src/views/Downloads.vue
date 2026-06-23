<template>
  <div class="min-h-0 overflow-x-hidden">
    <Navbar />

    <div class="mx-auto max-w-4xl px-4 py-4 sm:py-8 sm:px-6">
      <!-- Header -->
      <div class="mb-6 sm:mb-8 flex flex-wrap items-end justify-between gap-4 mobile-page-header">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">
            {{ t('library.title') }}
          </h1>
          <p class="mt-1 text-sm text-base-content/60">
            {{ t('library.subtitle') }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            v-if="files.length > 0"
            class="btn btn-primary btn-sm h-11 px-5 rounded-full"
            @click="playAll"
            :title="t('library.play')"
          >
            <Icon icon="clarity:play-line" class="h-4 w-4 mr-1.5" />
            {{ t('library.play') }}
          </button>
          <button
            class="btn btn-sm h-11 px-5 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
            @click="refresh"
            :disabled="loading"
          >
            <span
              v-if="loading"
              class="loading loading-spinner loading-xs mr-2"
            />
            <Icon v-else icon="clarity:refresh-line" class="h-4 w-4 mr-2" />
            {{ t('common.refresh') }}
          </button>
        </div>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="surface rounded-2xl p-4 mb-4 flex gap-3 items-center text-sm text-error"
      >
        <Icon icon="clarity:exclamation-circle-line" class="h-5 w-5 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading && files.length === 0" class="space-y-3">
        <div v-for="n in 4" :key="n" class="skeleton h-16 rounded-2xl" />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="files.length === 0"
        class="surface rounded-2xl p-12 flex flex-col items-center text-center"
      >
        <Icon
          icon="clarity:library-line"
          class="h-12 w-12 text-base-content/20 mb-4"
        />
        <p class="text-base-content/50 text-sm">{{ t('library.empty') }}</p>
        <p class="text-base-content/40 text-xs mt-1">
          {{ t('library.emptyHint') }}
        </p>
      </div>

      <div v-else>
        <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div
            class="inline-flex max-w-full overflow-x-auto rounded-full border border-white/10 bg-base-100/75 p-1"
          >
            <button
              class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              :class="
                viewMode === 'artists'
                  ? 'bg-primary text-primary-content shadow-glow-sm'
                  : 'text-base-content/60 hover:text-base-content'
              "
              @click="showArtists"
            >
              {{ t('library.artists') }}
            </button>
            <button
              class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              :class="
                viewMode === 'tracks'
                  ? 'bg-primary text-primary-content shadow-glow-sm'
                  : 'text-base-content/60 hover:text-base-content'
              "
              @click="showTracks"
            >
              {{ t('library.tracks') }}
            </button>
            <button
              class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              :class="
                viewMode === 'albums'
                  ? 'bg-primary text-primary-content shadow-glow-sm'
                  : 'text-base-content/60 hover:text-base-content'
              "
              @click="showAlbums"
            >
              {{ t('library.albums') }}
            </button>
          </div>
          <p class="text-xs text-base-content/45">
            {{
              t('library.artistCount', {
                artists: artists.length,
                albums: albums.length,
                tracks: files.length,
              })
            }}
          </p>
        </div>

        <!-- Artist cards -->
        <div
          v-if="viewMode === 'artists' && !selectedArtist"
          class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
        >
          <article
            v-for="artist in paginatedArtists"
            :key="artist.name"
            class="surface group cursor-pointer rounded-2xl p-4 text-left transition-transform hover:-translate-y-0.5 hover:border-primary/30"
            role="button"
            tabindex="0"
            @click="openArtist(artist.name)"
            @keydown.enter="openArtist(artist.name)"
            @keydown.space.prevent="openArtist(artist.name)"
          >
            <div class="mb-4 flex -space-x-3">
              <div
                v-for="file in artist.previewFiles"
                :key="file"
                class="relative h-12 w-12 overflow-hidden rounded-xl border border-base-100 bg-base-200/80"
              >
                <CoverImage
                  :key="file"
                  :src="coverSourcesFor(file).src"
                  :fallbacks="coverSourcesFor(file).fallbacks"
                  :alt="displayName(file)"
                  img-class="absolute inset-0 h-full w-full object-cover"
                >
                  <template #fallback>
                    <Icon
                      icon="clarity:music-note-line"
                      class="absolute left-1/2 top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 text-base-content/35"
                    />
                  </template>
                </CoverImage>
              </div>
            </div>
            <h2 class="truncate text-base font-semibold">
              {{ artist.name }}
            </h2>
            <p class="mt-1 text-xs text-base-content/50">
              {{
                t('library.artistMeta', {
                  tracks: artist.files.length,
                  albums: artist.albumCount,
                })
              }}
            </p>
            <p
              v-if="artist.albumNames.length"
              class="mt-3 max-h-10 overflow-hidden text-xs leading-5 text-base-content/45"
            >
              {{ artist.albumNames.slice(0, 3).join(' - ') }}
            </p>
            <div class="mt-4 flex items-center gap-2">
              <button
                class="icon-btn text-primary hover:bg-primary/10"
                @click.stop="playArtist(artist)"
                :title="t('library.playArtist')"
              >
                <Icon icon="clarity:play-line" class="h-4 w-4" />
              </button>
              <span class="text-xs text-primary/70 group-hover:text-primary">
                {{ t('library.openArtist') }}
              </span>
            </div>
          </article>
        </div>

        <div
          v-else-if="viewMode === 'artists' && selectedArtist && !selectedAlbum"
          class="mb-4 flex flex-wrap items-center justify-between gap-3"
        >
          <button
            class="btn btn-sm h-10 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
            @click="closeArtist"
          >
            <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-[-90deg]" />
            {{ t('library.backToArtists') }}
          </button>
          <div class="min-w-0 text-right">
            <h2 class="truncate text-lg font-semibold">
              {{ selectedArtist.name }}
            </h2>
            <p class="text-xs text-base-content/50">
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
          v-if="selectedAlbum"
          class="mb-4 flex flex-wrap items-center justify-between gap-3"
        >
          <button
            class="btn btn-sm h-10 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
            @click="closeAlbum"
          >
            <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-[-90deg]" />
            {{
              selectedArtist
                ? t('library.backToAlbums')
                : t('library.albums')
            }}
          </button>
          <div class="min-w-0 text-right">
            <h2 class="truncate text-lg font-semibold">
              {{ selectedAlbum.name }}
            </h2>
            <p class="truncate text-xs text-base-content/50">
              {{ selectedAlbum.artist }} -
              {{ t('library.albumMeta', { tracks: selectedAlbum.files.length }) }}
            </p>
          </div>
        </div>

        <!-- Album cards -->
        <div
          v-if="
            (viewMode === 'albums' || (viewMode === 'artists' && selectedArtist)) &&
            !selectedAlbum
          "
          class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
          :class="selectedArtist ? 'mb-5' : ''"
        >
          <article
            v-for="album in paginatedAlbums"
            :key="album.key"
            class="surface group cursor-pointer rounded-2xl p-4 text-left transition-transform hover:-translate-y-0.5 hover:border-primary/30"
            role="button"
            tabindex="0"
            @click="openAlbum(album)"
            @keydown.enter="openAlbum(album)"
            @keydown.space.prevent="openAlbum(album)"
          >
            <div
              class="relative mb-4 aspect-square overflow-hidden rounded-xl bg-base-200/80"
            >
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
                    class="absolute left-1/2 top-1/2 h-8 w-8 -translate-x-1/2 -translate-y-1/2 text-base-content/35"
                  />
                </template>
              </CoverImage>
            </div>
            <h2 class="truncate text-base font-semibold">
              {{ album.name }}
            </h2>
            <p class="mt-1 truncate text-xs text-primary/70">
              {{ album.artist }}
            </p>
            <p class="mt-1 text-xs text-base-content/50">
              {{ t('library.albumMeta', { tracks: album.files.length }) }}
            </p>
            <div class="mt-4 flex items-center gap-2">
              <button
                class="icon-btn text-primary hover:bg-primary/10"
                @click.stop="playAlbum(album)"
                :title="t('library.playAlbum')"
              >
                <Icon icon="clarity:play-line" class="h-4 w-4" />
              </button>
              <span class="text-xs text-primary/70 group-hover:text-primary">
                {{ t('library.openAlbum') }}
              </span>
            </div>
          </article>
        </div>

        <!-- File list -->
        <ul
          v-if="
            viewMode === 'tracks' ||
            selectedAlbum ||
            (selectedArtist && selectedArtistAlbums.length === 0)
          "
          class="space-y-2"
        >
          <li
            v-for="file in paginatedFiles"
            :key="file"
            class="surface rounded-2xl p-3 sm:p-4 flex items-center gap-3"
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
                  <div class="flex h-full w-full items-center justify-center text-base-content/35">
                    <Icon icon="clarity:music-note-line" class="h-5 w-5" />
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
                <span v-if="folderOf(file)" class="mr-2 text-primary/70">
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
                <Icon v-else icon="clarity:trash-line" class="h-4 w-4" />
              </button>
            </div>
          </li>
        </ul>
      </div>

      <!-- Pagination -->
      <nav
        v-if="totalPages > 1"
        class="mt-8 flex items-center justify-center gap-1 flex-wrap"
      >
        <button
          class="icon-btn"
          :disabled="currentPage === 1"
          @click="currentPage--"
          :title="t('common.previousPage')"
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
          :title="t('common.nextPage')"
        >
          <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-90" />
        </button>
      </nav>

      <!-- Count footer -->
      <p
        v-if="files.length > 0"
        class="mt-6 text-xs text-base-content/40 text-center"
      >
        {{
          files.length === 1
            ? t('library.countOne', { count: files.length })
            : t('library.countMany', { count: files.length })
        }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import { useRouter } from 'vue-router'
import Navbar from '/src/components/Navbar.vue'
import CoverImage from '/src/components/CoverImage.vue'
import API from '/src/model/api'
import { useI18n } from '/src/i18n'
import { usePlayer } from '/src/model/player'

const PAGE_SIZE = 10
const ARTIST_PAGE_SIZE = 24

const { t } = useI18n()
const player = usePlayer()
const router = useRouter()

const files = ref([])
const loading = ref(false)
const error = ref('')
const deleting = ref({})
const currentPage = ref(1)
const viewMode = ref('artists')
const selectedArtistName = ref('')
const selectedAlbumKey = ref('')

const albums = computed(() => {
  const grouped = new Map()

  for (const file of files.value) {
    const artistName = artistOf(file)
    const albumName = albumOf(file)
    if (!albumName) continue

    const key = albumKey(artistName, albumName)
    if (!grouped.has(key)) {
      grouped.set(key, {
        key,
        name: albumName,
        artist: artistName,
        files: [],
      })
    }

    grouped.get(key).files.push(file)
  }

  return Array.from(grouped.values())
    .map((album) => ({
      ...album,
      coverFile: album.files[0],
    }))
    .sort(
      (a, b) =>
        a.artist.localeCompare(b.artist) || a.name.localeCompare(b.name)
    )
})

const artists = computed(() => {
  const grouped = new Map()

  for (const file of files.value) {
    const artistName = artistOf(file)
    const albumName = albumOf(file)
    if (!grouped.has(artistName)) {
      grouped.set(artistName, {
        name: artistName,
        files: [],
        albums: new Set(),
      })
    }

    const artist = grouped.get(artistName)
    artist.files.push(file)
    if (albumName) artist.albums.add(albumName)
  }

  return Array.from(grouped.values())
    .map((artist) => ({
      name: artist.name,
      files: artist.files,
      albumCount: artist.albums.size,
      albumNames: Array.from(artist.albums).sort((a, b) =>
        a.localeCompare(b)
      ),
      previewFiles: artist.files.slice(0, 3),
    }))
    .sort((a, b) => a.name.localeCompare(b.name))
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

const visibleFiles = computed(() =>
  selectedAlbum.value
    ? selectedAlbum.value.files
    : selectedArtist.value
      ? selectedArtist.value.files
    : files.value
)

const totalPages = computed(() => {
  const browsingArtistAlbums =
    viewMode.value === 'artists' &&
    selectedArtist.value &&
    !selectedAlbum.value &&
    selectedArtistAlbums.value.length > 0
  const browsingAlbums = viewMode.value === 'albums' && !selectedAlbum.value
  const browsingArtists = viewMode.value === 'artists' && !selectedArtist.value
  const count = browsingArtists
    ? artists.value.length
    : browsingAlbums || browsingArtistAlbums
      ? visibleAlbums.value.length
    : visibleFiles.value.length
  const pageSize =
    browsingArtists || browsingAlbums || browsingArtistAlbums
      ? ARTIST_PAGE_SIZE
      : PAGE_SIZE
  return Math.ceil(count / pageSize)
})

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

const paginatedFiles = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return visibleFiles.value.slice(start, start + PAGE_SIZE)
})

const paginatedArtists = computed(() => {
  const start = (currentPage.value - 1) * ARTIST_PAGE_SIZE
  return artists.value.slice(start, start + ARTIST_PAGE_SIZE)
})

const paginatedAlbums = computed(() => {
  const start = (currentPage.value - 1) * ARTIST_PAGE_SIZE
  return visibleAlbums.value.slice(start, start + ARTIST_PAGE_SIZE)
})

watch(files, () => {
  currentPage.value = 1
})

watch([viewMode, selectedArtistName, selectedAlbumKey], () => {
  currentPage.value = 1
})

watch(totalPages, (pages) => {
  if (pages > 0 && currentPage.value > pages) {
    currentPage.value = pages
  }
})

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

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const res = await API.listDownloads()
    files.value = res.data || []
  } catch {
    error.value = t('library.failedLoad')
  } finally {
    loading.value = false
  }
}

async function onDelete(file) {
  if (!confirm(t('library.deletePrompt', { file }))) return
  deleting.value = { ...deleting.value, [file]: true }
  try {
    await API.deleteDownload(file)
    files.value = files.value.filter((f) => f !== file)
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
  const slash = file.lastIndexOf('/')
  return slash >= 0 ? file.slice(slash + 1) : file
}

function folderOf(file) {
  const slash = file.lastIndexOf('/')
  return slash >= 0 ? file.slice(0, slash) : ''
}

function pathParts(file) {
  return String(file || '')
    .split('/')
    .map((part) => part.trim())
    .filter(Boolean)
}

function artistOf(file) {
  const parts = pathParts(file)
  if (parts.length > 1) return parts[0]

  const name = displayName(file).replace(/\.[^/.]+$/, '')
  const separator = name.indexOf(' - ')
  if (separator > 0) return name.slice(0, separator).trim()

  return t('common.unknownArtist')
}

function albumOf(file) {
  const parts = pathParts(file)
  if (parts.length > 2) return parts[1]
  return ''
}

function albumKey(artist, album) {
  return `${artist}\u0000${album}`
}

function showArtists() {
  viewMode.value = 'artists'
  selectedArtistName.value = ''
  selectedAlbumKey.value = ''
}

function showAlbums() {
  viewMode.value = 'albums'
  selectedArtistName.value = ''
  selectedAlbumKey.value = ''
}

function showTracks() {
  viewMode.value = 'tracks'
  selectedArtistName.value = ''
  selectedAlbumKey.value = ''
}

function openArtist(name) {
  selectedArtistName.value = name
  selectedAlbumKey.value = ''
}

function closeArtist() {
  selectedArtistName.value = ''
  selectedAlbumKey.value = ''
}

function openAlbum(album) {
  selectedAlbumKey.value = album.key
}

function closeAlbum() {
  selectedAlbumKey.value = ''
}

function playFile(file) {
  const playlist = visibleFiles.value
  player.setPlaylist(playlist, { startIndex: playlist.indexOf(file) })
  router.push({ name: 'Player' })
}

function playArtist(artist) {
  player.setPlaylist(artist.files, { startIndex: 0 })
  router.push({ name: 'Player' })
}

function playAlbum(album) {
  player.setPlaylist(album.files, { startIndex: 0 })
  router.push({ name: 'Player' })
}

function playAll() {
  if (!files.value.length) return
  player.setPlaylist(files.value, { startIndex: 0 })
  router.push({ name: 'Player' })
}

onMounted(refresh)
</script>
