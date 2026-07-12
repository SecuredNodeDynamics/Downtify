<template>
  <section class="library-download-offers">
    <div class="library-download-offers-header">
      <Icon
        icon="clarity:cloud-download-line"
        class="h-5 w-5 shrink-0 text-primary"
      />
      <div class="min-w-0">
        <p class="text-sm font-semibold">{{ t('library.notInLibrary') }}</p>
        <p class="mt-0.5 text-xs text-base-content/50">
          {{ t('library.notInLibraryHint') }}
        </p>
      </div>
    </div>

    <div v-if="loading" class="space-y-2">
      <div v-for="n in 3" :key="n" class="skeleton h-16 rounded-2xl" />
      <p class="text-center text-xs text-base-content/45">
        {{ t('library.onlineSearchLoading') }}
      </p>
    </div>

    <div
      v-else-if="error"
      class="rounded-2xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error"
    >
      {{ t('library.onlineSearchError') }}
    </div>

    <div
      v-else-if="!downloadableItems.length"
      class="rounded-2xl border border-white/10 bg-white/5 px-4 py-6 text-center"
    >
      <p class="text-sm text-base-content/50">
        {{ t('library.onlineSearchEmpty') }}
      </p>
    </div>

    <ul v-else class="library-download-offers-list">
      <li
        v-for="(item, index) in downloadableItems"
        :key="itemKey(item, index)"
        class="library-download-offer"
      >
        <div class="library-download-offer-cover">
          <CoverImage
            v-if="item.cover_url"
            :src="coverSrc(item.cover_url)"
            :alt="item.name"
            img-class="absolute inset-0 h-full w-full object-cover"
          >
            <template #fallback>
              <Icon
                icon="clarity:music-note-line"
                class="h-5 w-5 text-base-content/35"
              />
            </template>
          </CoverImage>
          <Icon
            v-else
            icon="clarity:music-note-line"
            class="h-5 w-5 text-base-content/35"
          />
        </div>

        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-semibold">{{ item.name }}</p>
          <p class="truncate text-xs text-base-content/55">
            {{ artistsLabel(item) }}
          </p>
          <p
            v-if="item.media_type === 'album'"
            class="truncate text-[11px] text-base-content/45"
          >
            {{ albumTrackCountLabel(item) }}
          </p>
          <p
            v-else-if="item.album_name"
            class="truncate text-[11px] text-base-content/40"
          >
            {{ item.album_name }}
          </p>
        </div>

        <div class="flex shrink-0 flex-col items-end gap-1.5">
          <span class="library-download-offer-type">
            {{
              item.media_type === 'album'
                ? t('search.albumType')
                : t('search.trackType')
            }}
          </span>
          <button
            type="button"
            class="library-download-offer-button btn btn-primary btn-sm h-9 rounded-full px-3"
            :class="downloadButtonClass(item, index)"
            :disabled="isDownloadLocked(item, index)"
            @click="handleDownload(item, index)"
          >
            <Icon
              :icon="downloadButtonIcon(item, index)"
              class="h-4 w-4"
            />
            <span class="sm:inline">{{ downloadButtonLabel(item, index) }}</span>
          </button>
        </div>
      </li>
    </ul>

    <p
      v-if="!loading && items.length > visibleItems.length"
      class="text-center text-xs text-base-content/40"
    >
      {{
        t('library.onlineSearchMore', {
          count: items.length - visibleItems.length,
        })
      }}
    </p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

import CoverImage from './CoverImage.vue'
import API from '../model/api'
import { useAlbumTrackCounts } from '../model/albumTrackCounts'
import {
  getLibraryDownloadOfferState,
  libraryDownloadOfferKey,
  setLibraryDownloadOfferState,
} from '../model/libraryDownloadOfferState'
import { onlineArtistsLabel } from '../model/libraryOnlineSearch'
import { useLibraryOwnership } from '../model/libraryOwnership'
import { useProgressTracker } from '../model/download'
import { useI18n } from '../i18n'

const props = defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  limit: { type: Number, default: 10 },
})

const emit = defineEmits(['download'])

const { t } = useI18n()
const pt = useProgressTracker()
const MIN_STARTING_MS = 900
const STARTING_TIMEOUT_MS = 30000
const RESET_FAILED_MS = 2500

const visibleItems = computed(() =>
  (props.items || []).slice(0, Math.max(1, props.limit))
)
const { isOwned } = useLibraryOwnership(visibleItems)
const downloadableItems = computed(() =>
  visibleItems.value.filter((item, index) => {
    if (!isOwned(item)) return true
    setLibraryDownloadOfferState(item, '', `offer-${index}`)
    return false
  })
)
const { trackCountFor } = useAlbumTrackCounts(visibleItems)

function coverSrc(url) {
  return API.mediaUrl(url)
}

function artistsLabel(item) {
  const label = onlineArtistsLabel(item)
  return label || t('common.unknownArtist')
}

function trackCountLabel(count) {
  const n = Number(count)
  if (!Number.isFinite(n) || n < 1) return ''
  return n === 1
    ? t('search.trackCountOne', { count: n })
    : t('search.trackCountMany', { count: n })
}

function albumTrackCountLabel(item) {
  const count = trackCountFor(item)
  return trackCountLabel(count) || `${t('search.tracksTag')} ...`
}

function itemKey(item, index) {
  return libraryDownloadOfferKey(item, `offer-${index}`)
}

function itemStateKey(item, index = 0) {
  return libraryDownloadOfferKey(item, `offer-${index}`)
}

function isQueued(item) {
  return Boolean(pt.getBySong(item))
}

function downloadState(item, index = 0) {
  if (isQueued(item)) return 'queued'
  return getLibraryDownloadOfferState(item, `offer-${index}`)
}

function isDownloadLocked(item, index) {
  return ['starting', 'queued', 'added'].includes(downloadState(item, index))
}

function downloadButtonIcon(item, index) {
  const state = downloadState(item, index)
  if (state === 'starting') return 'clarity:sync-line'
  if (state === 'queued' || state === 'added') return 'clarity:check-circle-line'
  if (state === 'failed') return 'clarity:error-standard-line'
  return 'clarity:download-line'
}

function downloadButtonLabel(item, index) {
  const state = downloadState(item, index)
  if (state === 'starting') return t('library.downloadStarting')
  if (state === 'queued') return t('search.inQueue')
  if (state === 'added') return t('library.downloadAdded')
  if (state === 'failed') return t('library.downloadFailed')
  return item.media_type === 'album'
    ? t('library.downloadAlbum')
    : t('library.downloadTrack')
}

function downloadButtonClass(item, index) {
  const state = downloadState(item, index)
  return {
    'library-download-offer-button-starting': state === 'starting',
    'library-download-offer-button-confirmed':
      state === 'queued' || state === 'added',
    'library-download-offer-button-failed': state === 'failed',
  }
}

function setDownloadStateAfterPress(key, state, pressedAt) {
  const elapsed = Date.now() - pressedAt
  window.setTimeout(
    () => {
      setLibraryDownloadOfferState(null, state, key)
    },
    Math.max(0, MIN_STARTING_MS - elapsed)
  )
}

function handleDownload(item, index) {
  const key = itemStateKey(item, index)
  const pressedAt = Date.now()
  setLibraryDownloadOfferState(item, 'starting', key)
  const timeout = window.setTimeout(() => {
    if (getLibraryDownloadOfferState(item, key) !== 'starting') return
    setLibraryDownloadOfferState(item, 'failed', key)
    window.setTimeout(() => {
      if (getLibraryDownloadOfferState(item, key) === 'failed') {
        setLibraryDownloadOfferState(item, '', key)
      }
    }, RESET_FAILED_MS)
  }, STARTING_TIMEOUT_MS)
  emit('download', item, {
    queued: () => {
      window.clearTimeout(timeout)
      setDownloadStateAfterPress(key, 'queued', pressedAt)
    },
    added: () => {
      window.clearTimeout(timeout)
      setDownloadStateAfterPress(key, 'added', pressedAt)
    },
    failed: () => {
      window.clearTimeout(timeout)
      setDownloadStateAfterPress(key, 'failed', pressedAt)
      window.setTimeout(() => {
        if (getLibraryDownloadOfferState(item, key) === 'failed') {
          setLibraryDownloadOfferState(item, '', key)
        }
      }, RESET_FAILED_MS)
    },
  })
}
</script>

<style scoped>
.library-download-offers {
  @apply mt-3 space-y-3;
}

.library-download-offers-header {
  @apply flex items-start gap-3 rounded-2xl border border-primary/20 bg-primary/5 px-3 py-3;
}

.library-download-offers-list {
  @apply space-y-2;
}

.library-download-offer {
  @apply flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-3;
}

.library-download-offer-cover {
  @apply relative flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-base-200/80;
}

.library-download-offer-type {
  @apply rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-base-content/55;
}

.library-download-offer-button {
  @apply relative min-w-32 overflow-hidden transition-all duration-200 active:scale-95;
}

.library-download-offer-button-starting {
  @apply scale-[1.03] ring-2 ring-primary/60 ring-offset-2 ring-offset-base-100;
  animation: library-download-button-pulse 0.8s ease-in-out infinite;
}

.library-download-offer-button-starting::after {
  content: '';
  position: absolute;
  inset: -40% -60%;
  background: linear-gradient(
    100deg,
    transparent 35%,
    rgba(255, 255, 255, 0.42) 50%,
    transparent 65%
  );
  animation: library-download-sheen 0.95s linear infinite;
}

.library-download-offer-button-starting :deep(svg) {
  animation: library-download-spin 0.9s linear infinite;
}

.library-download-offer-button-confirmed {
  @apply bg-emerald-400 text-black shadow-glow-sm ring-2 ring-emerald-200/70;
  animation: library-download-confirm-pop 0.36s ease-out both;
}

.library-download-offer-button-failed {
  @apply bg-error text-error-content ring-2 ring-error/60;
  animation: library-download-confirm-pop 0.28s ease-out both;
}

@keyframes library-download-button-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.48);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(34, 197, 94, 0);
  }
}

@keyframes library-download-sheen {
  from {
    transform: translateX(-55%);
  }
  to {
    transform: translateX(55%);
  }
}

@keyframes library-download-confirm-pop {
  0% {
    transform: scale(0.96);
  }
  70% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes library-download-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
