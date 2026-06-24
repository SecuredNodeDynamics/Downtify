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
      v-else-if="!items.length"
      class="rounded-2xl border border-white/10 bg-white/5 px-4 py-6 text-center"
    >
      <p class="text-sm text-base-content/50">
        {{ t('library.onlineSearchEmpty') }}
      </p>
    </div>

    <ul v-else class="library-download-offers-list">
      <li
        v-for="(item, index) in visibleItems"
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
          <p v-if="item.album_name" class="truncate text-[11px] text-base-content/40">
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
            class="btn btn-primary btn-sm h-9 rounded-full px-3"
            :disabled="isQueued(item)"
            @click="emit('download', item)"
          >
            <Icon
              :icon="
                isQueued(item) ? 'clarity:check-circle-line' : 'clarity:download-line'
              "
              class="h-4 w-4"
            />
            <span class="sm:inline">{{
              isQueued(item)
                ? t('search.inQueue')
                : item.media_type === 'album'
                ? t('library.downloadAlbum')
                : t('library.downloadTrack')
            }}</span>
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
import { onlineArtistsLabel } from '../model/libraryOnlineSearch'
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

const visibleItems = computed(() =>
  (props.items || []).slice(0, Math.max(1, props.limit))
)

function coverSrc(url) {
  return API.mediaUrl(url)
}

function artistsLabel(item) {
  const label = onlineArtistsLabel(item)
  return label || t('common.unknownArtist')
}

function itemKey(item, index) {
  return item?.browse_id || item?.song_id || item?.url || `offer-${index}`
}

function isQueued(item) {
  return Boolean(pt.getBySong(item))
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
</style>
