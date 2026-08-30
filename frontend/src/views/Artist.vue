<template>
  <div class="min-h-0 overflow-x-hidden">
    <Navbar />
    <div class="mx-auto max-w-4xl px-4 py-4 sm:px-6 sm:py-8">
      <div class="mb-5 flex items-start gap-3 mobile-page-header">
        <button
          type="button"
          class="icon-btn mt-0.5 shrink-0"
          :title="t('nav.back')"
          @click="goBack"
        >
          <Icon icon="clarity:angle-line" class="h-5 w-5 rotate-[-90deg]" />
        </button>
        <div class="min-w-0 flex-1">
          <h1 class="truncate text-2xl font-bold tracking-tight">
            {{ artistName || t('artist.title') }}
          </h1>
          <p class="mt-1 text-sm text-base-content/60">
            {{ t('artist.subtitle') }}
          </p>
        </div>
        <LibraryArtistMonitor v-if="artistName" :artist-name="artistName" />
      </div>

      <div v-if="loading" class="space-y-3">
        <div class="skeleton h-24 rounded-2xl" />
        <div class="skeleton h-24 rounded-2xl" />
      </div>

      <div
        v-else-if="error"
        class="surface rounded-2xl p-4 text-sm text-error"
      >
        {{ error }}
      </div>

      <ul v-else-if="albums.length" class="space-y-2">
        <li
          v-for="album in albums"
          :key="album.browse_id || album.name"
          class="surface flex items-center gap-3 rounded-2xl p-3 sm:p-4"
        >
          <div class="relative h-14 w-14 shrink-0 overflow-hidden rounded-xl">
            <CoverImage
              v-if="album.cover_url"
              :src="coverSrc(album.cover_url)"
              :alt="album.name"
              img-class="h-full w-full object-cover"
            />
            <div
              v-else
              class="flex h-full w-full items-center justify-center bg-base-content/10"
            >
              <Icon icon="clarity:album-line" class="h-6 w-6" />
            </div>
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold">{{ album.name }}</p>
            <p class="truncate text-xs text-base-content/55">
              {{ albumMeta(album) }}
            </p>
          </div>
          <button
            v-if="albumStatus(album).kind === 'owned'"
            type="button"
            class="btn btn-sm rounded-full"
            @click="viewAlbum(album)"
          >
            {{ t('search.viewAlbum') }}
          </button>
          <button
            v-else
            type="button"
            class="btn btn-primary btn-sm rounded-full"
            :disabled="isQueued(album)"
            @click="downloadAlbum(album)"
          >
            {{
              albumStatus(album).kind === 'remaining'
                ? t('search.downloadRemaining')
                : t('search.downloadAlbum')
            }}
          </button>
        </li>
      </ul>

      <div
        v-else
        class="surface rounded-2xl p-12 text-center text-sm text-base-content/50"
      >
        {{ t('artist.empty') }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'Artist' })
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'

import Navbar from '/src/components/Navbar.vue'
import CoverImage from '/src/components/CoverImage.vue'
import LibraryArtistMonitor from '/src/components/LibraryArtistMonitor.vue'
import API from '../model/api'
import { albumLibraryStatus } from '../model/albumDownload'
import { useDownloadManager, useProgressTracker } from '../model/download'
import { useAlbumTrackCounts } from '../model/albumTrackCounts'
import {
  libraryNavigationForAlbum,
  setLibraryNavigation,
} from '../model/libraryNavigation'
import { findLibraryAlbum } from '../model/libraryOwnership'
import { getCachedLibraryItems } from '../model/librarySession'
import { useI18n } from '../i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const dm = useDownloadManager()
const pt = useProgressTracker()

const loading = ref(false)
const error = ref('')
const page = ref(null)
const albums = computed(() =>
  Array.isArray(page.value?.albums) ? page.value.albums : []
)
const { trackCountFor } = useAlbumTrackCounts(albums)
const artistName = computed(
  () => page.value?.name || String(route.query.name || '').trim()
)

function coverSrc(url) {
  return API.mediaUrl(url)
}

function albumMeta(album) {
  const count = trackCountFor(album) || album.track_count
  const status = albumStatus(album)
  const year = album.year || ''
  const countLabel = count
    ? t(count === 1 ? 'search.trackCountOne' : 'search.trackCountMany', {
        count,
      })
    : ''
  if (status.kind === 'remaining' && status.expected) {
    return t('player.albumCompleteness', {
      have: status.have,
      total: status.expected,
    })
  }
  return [year, countLabel].filter(Boolean).join(' · ')
}

function albumStatus(album) {
  return albumLibraryStatus(album, getCachedLibraryItems() || [])
}

function isQueued(album) {
  return Boolean(pt.getBySong(album))
}

function downloadAlbum(album) {
  void dm.queue(album)
}

function viewAlbum(album) {
  const libraryAlbum = findLibraryAlbum(album, getCachedLibraryItems() || [])
  const navigation = libraryNavigationForAlbum(libraryAlbum)
  if (!navigation) return
  setLibraryNavigation(navigation)
  router.push({ name: 'List' })
}

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push({ name: 'Search' })
}

async function loadArtist() {
  loading.value = true
  error.value = ''
  try {
    const res = await API.getArtist({
      browseId: route.params.browseId || '',
      name: route.query.name || '',
    })
    page.value = res.data
  } catch (err) {
    page.value = null
    error.value = err?.response?.data?.detail || t('artist.loadError')
  } finally {
    loading.value = false
  }
}

watch(
  () => [route.params.browseId, route.query.name],
  loadArtist,
  { immediate: true }
)
</script>
