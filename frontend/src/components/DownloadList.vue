<template>
  <div class="queue-page">
    <div class="queue-chrome">
      <ServerConnectionPrompt class="mb-3" />

      <div class="queue-toolbar">
        <div class="queue-tabs">
          <button
            type="button"
            class="queue-tab-btn"
            :class="
              activeTab === 'queue'
                ? 'queue-tab-btn-active'
                : 'queue-tab-btn-inactive'
            "
            @click="activeTab = 'queue'"
          >
            {{ t('queue.tab') }}
            <span
              v-if="pt.downloadQueue.value.length > 0"
              class="queue-tab-count"
            >
              {{ pt.downloadQueue.value.length }}
            </span>
          </button>
          <button
            type="button"
            class="queue-tab-btn"
            :class="
              activeTab === 'history'
                ? 'queue-tab-btn-active'
                : 'queue-tab-btn-inactive'
            "
            @click="activeTab = 'history'"
          >
            {{ t('history.tab') }}
          </button>
        </div>

        <button
          v-if="activeTab === 'queue' && pt.downloadQueue.value.length > 0"
          type="button"
          class="queue-action-btn text-error/70 hover:text-error"
          @click="onClearAll"
          :title="t('queue.clearAll')"
        >
          <Icon icon="clarity:trash-line" class="h-4 w-4" />
          <span class="hidden sm:inline">{{ t('queue.clearAll') }}</span>
        </button>

        <template v-else-if="activeTab === 'history'">
          <button
            type="button"
            class="queue-action-btn"
            @click="refreshHistory"
            :disabled="historyLoading"
            :title="t('common.refresh')"
          >
            <span
              v-if="historyLoading"
              class="loading loading-spinner loading-xs"
            />
            <Icon v-else icon="clarity:refresh-line" class="h-4 w-4" />
            <span class="hidden sm:inline">{{ t('common.refresh') }}</span>
          </button>
          <button
            v-if="history.length > 0"
            type="button"
            class="queue-action-btn text-error/70 hover:text-error"
            @click="onClearHistory"
            :title="t('history.clear')"
          >
            <Icon icon="clarity:trash-line" class="h-4 w-4" />
            <span class="hidden sm:inline">{{ t('history.clear') }}</span>
          </button>
        </template>
      </div>
    </div>

    <div class="queue-body-slot">
      <div
        class="panel-glow-shell panel-glow-shell-grow surface min-h-0 rounded-3xl"
      >
        <div class="queue-panel panel-glow-inner p-3 sm:p-5">
          <div class="queue-scroll-body">
            <template v-if="activeTab === 'queue'">
              <div
                v-if="pt.downloadQueue.value.length === 0"
                class="queue-empty"
              >
                <Icon
                  icon="clarity:download-line"
                  class="mb-4 h-12 w-12 text-base-content/20"
                />
                <p class="text-sm text-base-content/50">
                  {{ t('queue.empty') }}
                </p>
                <p class="mt-1 text-xs text-base-content/40">
                  {{ t('queue.emptyHint') }}
                </p>
              </div>

              <ul v-else class="queue-list">
                <li
                  v-for="item in pt.downloadQueue.value"
                  :key="item.song.song_id || item.song.name"
                  class="queue-item"
                >
                  <div class="queue-item-cover">
                    <CoverImage
                      v-if="item.song.cover_url"
                      :src="coverSrc(item.song.cover_url)"
                      :alt="item.song.name"
                      img-class="h-full w-full object-cover"
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
                    <div class="mb-0.5 flex items-center gap-2">
                      <span class="truncate text-sm font-semibold">
                        {{ item.song.name }}
                      </span>
                      <span :class="statusClass(item)" class="shrink-0">
                        {{ item.message || item.web_status }}
                      </span>
                    </div>
                    <p class="truncate text-xs text-base-content/60">
                      {{ artistsOf(item.song) }}
                    </p>
                    <p
                      v-if="item.song.album_name"
                      class="truncate text-xs text-base-content/40"
                    >
                      {{ item.song.album_name }}
                    </p>
                  </div>

                  <div class="flex shrink-0 items-center gap-1">
                    <a
                      v-if="item.isDownloaded() && !dd.isLocal.value"
                      class="icon-btn text-primary hover:bg-primary/10"
                      href="javascript:;"
                      @click="forceDownload(item.web_download_url)"
                      :title="t('queue.saveToDevice')"
                    >
                      <Icon icon="clarity:download-line" class="h-4 w-4" />
                    </a>
                    <div
                      v-else-if="item.progress > 0 && !item.isErrored()"
                      class="radial-progress text-primary"
                      :style="`--value:${item.progress}; --size:2.5rem; --thickness:3px`"
                    >
                      <span class="text-[10px] font-semibold">
                        {{ Math.round(item.progress) }}%
                      </span>
                    </div>
                    <span
                      v-else-if="!item.isErrored()"
                      class="loading loading-spinner loading-sm text-primary"
                    />

                    <button
                      type="button"
                      class="icon-btn text-error/70 hover:bg-error/10 hover:text-error"
                      @click="dm.remove(item.song)"
                      :title="t('queue.removeFromQueue')"
                    >
                      <Icon icon="clarity:trash-line" class="h-4 w-4" />
                    </button>
                  </div>
                </li>
              </ul>
            </template>

            <template v-else>
              <div
                v-if="historyError"
                class="mb-3 flex items-center gap-3 rounded-2xl border border-error/20 bg-error/10 p-3 text-sm text-error"
              >
                <Icon
                  icon="clarity:exclamation-circle-line"
                  class="h-5 w-5 shrink-0"
                />
                <span>{{ historyError }}</span>
              </div>

              <div v-if="historyLoading && history.length === 0" class="space-y-2">
                <div
                  v-for="n in 4"
                  :key="n"
                  class="skeleton h-16 rounded-2xl"
                />
              </div>

              <div v-else-if="history.length === 0" class="queue-empty">
                <Icon
                  icon="clarity:history-line"
                  class="mb-4 h-10 w-10 text-base-content/20"
                />
                <p class="text-sm text-base-content/50">
                  {{ t('history.empty') }}
                </p>
                <p class="mt-1 text-xs text-base-content/40">
                  {{ t('history.emptyHint') }}
                </p>
              </div>

              <ul v-else class="queue-list">
                <li
                  v-for="item in sortedHistory"
                  :key="item.id"
                  class="queue-item"
                  :class="{ 'queue-item-playable': canOpenHistoryInPlayer(item) }"
                >
                  <button
                    v-if="canOpenHistoryInPlayer(item)"
                    type="button"
                    class="queue-item-main"
                    :title="t('history.openInPlayer')"
                    @click="openHistoryInPlayer(item)"
                  >
                    <div class="queue-item-cover">
                      <CoverImage
                        v-if="item.song?.cover_url"
                        :src="coverSrc(item.song.cover_url)"
                        :alt="item.title"
                        img-class="h-full w-full object-cover"
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

                    <div class="min-w-0 flex-1 text-left">
                      <div class="mb-0.5 flex items-center gap-2">
                        <span class="truncate text-sm font-semibold">
                          {{ item.title || t('common.unknownTrack') }}
                        </span>
                        <span :class="historyStatusClass(item)" class="shrink-0">
                          {{ historyStatusLabel(item) }}
                        </span>
                      </div>
                      <p class="truncate text-xs text-base-content/60">
                        {{ item.artists || t('common.unknownArtist') }}
                      </p>
                      <p class="truncate text-xs text-base-content/40">
                        {{ formatDate(historyDate(item)) }}
                      </p>
                    </div>
                  </button>

                  <template v-else>
                    <div class="queue-item-cover">
                      <CoverImage
                        v-if="item.song?.cover_url"
                        :src="coverSrc(item.song.cover_url)"
                        :alt="item.title"
                        img-class="h-full w-full object-cover"
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
                      <div class="mb-0.5 flex items-center gap-2">
                        <span class="truncate text-sm font-semibold">
                          {{ item.title || t('common.unknownTrack') }}
                        </span>
                        <span :class="historyStatusClass(item)" class="shrink-0">
                          {{ historyStatusLabel(item) }}
                        </span>
                      </div>
                      <p class="truncate text-xs text-base-content/60">
                        {{ item.artists || t('common.unknownArtist') }}
                      </p>
                      <p class="truncate text-xs text-base-content/40">
                        {{ formatDate(historyDate(item)) }}
                        <span v-if="item.error">- {{ item.error }}</span>
                      </p>
                    </div>
                  </template>

                  <div class="flex shrink-0 items-center gap-1">
                    <a
                      v-if="item.filename"
                      class="icon-btn"
                      :href="API.downloadFileURL(item.filename)"
                      download
                      :title="t('history.downloadFile')"
                    >
                      <Icon icon="clarity:download-line" class="h-4 w-4" />
                    </a>
                    <button
                      v-if="item.status === 'error'"
                      type="button"
                      class="icon-btn text-primary hover:bg-primary/10"
                      :disabled="retrying[item.id] === true"
                      @click="retryHistory(item)"
                      :title="t('history.retry')"
                    >
                      <span
                        v-if="retrying[item.id] === true"
                        class="loading loading-spinner loading-xs"
                      />
                      <Icon v-else icon="clarity:refresh-line" class="h-4 w-4" />
                    </button>
                  </div>
                </li>
              </ul>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import API from '../model/api'
import CoverImage from './CoverImage.vue'
import ServerConnectionPrompt from './ServerConnectionPrompt.vue'
import { useProgressTracker, useDownloadManager } from '../model/download'
import { useDownloadDestination } from '../model/downloadDestination'
import {
  canOpenHistoryInPlayer,
  setPlayerNavigation,
} from '../model/playerNavigation'
import { useI18n } from '../i18n'

const router = useRouter()

const pt = useProgressTracker()
const dm = useDownloadManager()
const dd = useDownloadDestination()
const { t } = useI18n()
const activeTab = ref('queue')
const history = ref([])
const historyLoading = ref(false)
const historyError = ref('')
const retrying = ref({})
let historyRefreshTimer = 0
let historyFetchSeq = 0

function coverSrc(url) {
  return API.mediaUrl(url)
}

async function onClearAll() {
  if (!confirm(t('queue.clearAllPrompt'))) return
  await dm.clearAll()
}

function artistsOf(song) {
  if (Array.isArray(song.artists) && song.artists.length) {
    return song.artists.join(', ')
  }
  return song.artist || t('common.unknownArtist')
}

function statusClass(item) {
  if (item.isErrored()) return 'badge-error-soft'
  if (item.isDownloaded()) return 'badge-soft'
  return 'badge-neutral-soft'
}

function historyStatusClass(item) {
  if (item.status === 'error') return 'badge-error-soft'
  if (item.status === 'done') return 'badge-soft'
  return 'badge-neutral-soft'
}

function historyStatusLabel(item) {
  if (item.status === 'error') return t('history.failed')
  if (item.status === 'done') return t('history.done')
  if (item.status === 'skipped') return t('history.skipped')
  if (item.status === 'downloading') return t('history.downloading')
  return t('history.queued')
}

function historyDate(item) {
  return item.completed_at || item.updated_at || item.created_at || ''
}

function historySortKey(item) {
  return historyDate(item)
}

function sortHistoryItems(items) {
  return [...items].sort((a, b) => {
    const cmp = historySortKey(b).localeCompare(historySortKey(a))
    if (cmp !== 0) return cmp
    return (b.id || 0) - (a.id || 0)
  })
}

const sortedHistory = computed(() => sortHistoryItems(history.value))

function formatDate(value) {
  if (!value) return ''
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

async function refreshHistory() {
  const seq = ++historyFetchSeq
  historyLoading.value = true
  historyError.value = ''
  try {
    const res = await API.getHistory()
    if (seq !== historyFetchSeq) return
    history.value = sortHistoryItems(
      Array.isArray(res.data) ? res.data : []
    )
  } catch {
    if (seq !== historyFetchSeq) return
    historyError.value = t('history.failedLoad')
  } finally {
    if (seq === historyFetchSeq) {
      historyLoading.value = false
    }
  }
}

function scheduleRefreshHistory() {
  if (historyRefreshTimer) {
    clearTimeout(historyRefreshTimer)
  }
  historyRefreshTimer = setTimeout(() => {
    historyRefreshTimer = 0
    void refreshHistory()
  }, 250)
}

async function retryHistory(item) {
  retrying.value = { ...retrying.value, [item.id]: true }
  try {
    await API.retryHistoryItem(item.id)
    await refreshHistory()
  } catch {
    historyError.value = t('history.failedRetry')
  } finally {
    retrying.value = { ...retrying.value, [item.id]: false }
  }
}

async function onClearHistory() {
  if (!confirm(t('history.clearPrompt'))) return
  await API.clearHistory()
  history.value = []
}

function forceDownload(url) {
  const a = document.createElement('a')
  a.href = url
  a.download = url.split('/').pop()
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function openHistoryInPlayer(item) {
  if (!canOpenHistoryInPlayer(item)) return
  setPlayerNavigation({
    file: item.filename,
    artist: item.artists || '',
    album: item.album || '',
  })
  router.push({ name: 'Player' })
}

watch(
  () => pt.historyRevision.value,
  () => {
    scheduleRefreshHistory()
  }
)

watch(activeTab, (tab) => {
  if (tab === 'history') void refreshHistory()
})

onMounted(refreshHistory)

onActivated(() => {
  void refreshHistory()
})
</script>

<style scoped>
.queue-page {
  @apply mx-auto flex w-full max-w-4xl flex-1 flex-col gap-2 min-h-0 px-4 py-3 sm:px-6 lg:py-8;
}

.queue-chrome {
  @apply shrink-0 space-y-3;
}

.queue-toolbar {
  @apply flex items-center gap-2;
}

.queue-tabs {
  @apply inline-flex min-w-0 flex-1 gap-1 overflow-x-auto rounded-full border border-white/10 bg-base-100/75 p-1;
}

.queue-tab-btn {
  @apply flex flex-1 items-center justify-center gap-1.5 whitespace-nowrap rounded-full px-3 py-2 text-center text-sm font-medium transition-colors sm:px-4;
}

.queue-tab-btn-active {
  @apply bg-primary text-primary-content shadow-glow-sm;
}

.queue-tab-btn-inactive {
  @apply text-base-content/65 hover:bg-white/5 hover:text-base-content;
}

.queue-tab-count {
  @apply inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-primary-content/15 px-1.5 text-[11px] font-semibold;
}

.queue-action-btn {
  @apply inline-flex h-10 shrink-0 items-center gap-1.5 rounded-full border border-white/10 bg-base-100/85 px-3 text-sm font-medium transition-colors hover:bg-base-100;
}

.queue-body-slot {
  @apply flex min-h-0 flex-1 flex-col;
}

.queue-panel {
  @apply flex min-h-0 flex-1 flex-col;
}

.queue-scroll-body {
  @apply min-h-0 flex-1 overflow-x-hidden overflow-y-auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.queue-scroll-body::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.queue-empty {
  @apply flex flex-col items-center px-4 py-12 text-center sm:py-16;
}

.queue-list {
  @apply space-y-2;
}

.queue-item {
  @apply flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 transition-colors sm:gap-4 sm:p-3.5;
}

.queue-item-playable {
  @apply hover:border-primary/25 hover:bg-white/[0.07] active:bg-white/10;
}

.queue-item-main {
  @apply flex min-w-0 flex-1 items-center gap-3 text-left sm:gap-4;
}

.queue-item-cover {
  @apply relative flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-primary/10 text-primary sm:h-12 sm:w-12;
}

@media (min-width: 1024px) {
  .queue-page {
    @apply gap-4 py-8;
  }

  .queue-chrome {
    @apply sticky top-16 z-20 -mx-6 bg-base-100/90 px-6 pb-3 backdrop-blur-md;
  }

  .queue-body-slot {
    flex: none;
  }

  .queue-panel {
    flex: none;
    min-height: auto;
  }

  .queue-scroll-body {
    overflow: visible;
    max-height: none;
  }
}
</style>
