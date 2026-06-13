<template>
  <div class="mx-auto max-w-4xl px-4 py-8 sm:px-6">
    <!-- Header -->
    <div class="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">
          {{ t('queue.title') }}
        </h1>
        <p class="mt-1 text-sm text-base-content/60">
          {{ t('queue.subtitle') }}
        </p>
      </div>
      <button
        v-if="pt.downloadQueue.value.length > 0"
        class="btn btn-sm h-11 px-5 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100 text-error/70 hover:text-error"
        @click="onClearAll"
        :title="t('queue.clearAll')"
      >
        <Icon icon="clarity:trash-line" class="h-4 w-4 mr-1.5" />
        {{ t('queue.clearAll') }}
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="pt.downloadQueue.value.length === 0"
      class="surface rounded-2xl p-12 flex flex-col items-center text-center"
    >
      <Icon
        icon="clarity:download-line"
        class="h-12 w-12 text-base-content/20 mb-4"
      />
      <p class="text-base-content/50 text-sm">{{ t('queue.empty') }}</p>
      <p class="text-base-content/40 text-xs mt-1">
        {{ t('queue.emptyHint') }}
      </p>
    </div>

    <!-- Queue items -->
    <ul v-else class="space-y-3">
      <li
        v-for="(item, index) in paginatedQueue"
        :key="index"
        class="surface rounded-2xl p-3 sm:p-4 flex items-center gap-4"
      >
        <!-- Cover -->
        <div class="track-cover h-16 w-16 sm:h-20 sm:w-20">
          <img
            v-if="item.song.cover_url"
            :src="item.song.cover_url"
            :alt="item.song.name"
            class="h-full w-full object-cover"
          />
          <div
            v-else
            class="h-full w-full flex items-center justify-center text-base-content/30"
          >
            <Icon icon="clarity:music-note-line" class="h-6 w-6" />
          </div>
        </div>

        <!-- Title + status -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-0.5">
            <span class="font-semibold truncate">{{ item.song.name }}</span>
            <span :class="statusClass(item)" class="shrink-0">
              {{ item.message || item.web_status }}
            </span>
          </div>
          <p class="text-xs text-base-content/60 truncate">
            {{ artistsOf(item.song) }}
          </p>
          <p
            v-if="item.song.album_name"
            class="text-xs text-base-content/40 truncate"
          >
            {{ item.song.album_name }}
          </p>
        </div>

        <!-- Progress / actions -->
        <div class="flex items-center gap-2 shrink-0">
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
            :style="`--value:${item.progress}; --size:2.75rem; --thickness:3px`"
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
            class="icon-btn text-error/70 hover:text-error hover:bg-error/10"
            @click="dm.remove(item.song)"
            :title="t('queue.removeFromQueue')"
          >
            <Icon icon="clarity:trash-line" class="h-4 w-4" />
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
        :title="t('common.previousPage')"
      >
        <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-[-90deg]" />
      </button>
      <button
        v-for="page in totalPages"
        :key="page"
        class="h-10 min-w-[2.5rem] rounded-full px-3 text-sm font-medium transition-colors"
        :class="
          page === currentPage
            ? 'bg-primary text-primary-content shadow-glow-sm'
            : 'text-base-content/70 hover:text-base-content hover:bg-white/10'
        "
        @click="currentPage = page"
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

    <!-- History -->
    <section class="mt-12">
      <div class="mb-5 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 class="text-xl font-bold tracking-tight">
            {{ t('history.title') }}
          </h2>
          <p class="mt-1 text-sm text-base-content/60">
            {{ t('history.subtitle') }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="btn btn-sm h-10 px-4 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
            @click="refreshHistory"
            :disabled="historyLoading"
            :title="t('common.refresh')"
          >
            <span
              v-if="historyLoading"
              class="loading loading-spinner loading-xs mr-2"
            />
            <Icon v-else icon="clarity:refresh-line" class="h-4 w-4 mr-2" />
            {{ t('common.refresh') }}
          </button>
          <button
            v-if="history.length > 0"
            class="btn btn-sm h-10 px-4 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100 text-error/70 hover:text-error"
            @click="onClearHistory"
            :title="t('history.clear')"
          >
            <Icon icon="clarity:trash-line" class="h-4 w-4 mr-1.5" />
            {{ t('history.clear') }}
          </button>
        </div>
      </div>

      <div
        v-if="historyError"
        class="surface rounded-2xl p-4 mb-4 flex gap-3 items-center text-sm text-error"
      >
        <Icon icon="clarity:exclamation-circle-line" class="h-5 w-5 shrink-0" />
        <span>{{ historyError }}</span>
      </div>

      <div v-if="historyLoading && history.length === 0" class="space-y-3">
        <div v-for="n in 4" :key="n" class="skeleton h-16 rounded-2xl" />
      </div>

      <div
        v-else-if="history.length === 0"
        class="surface rounded-2xl p-10 flex flex-col items-center text-center"
      >
        <Icon
          icon="clarity:history-line"
          class="h-10 w-10 text-base-content/20 mb-4"
        />
        <p class="text-base-content/50 text-sm">{{ t('history.empty') }}</p>
        <p class="text-base-content/40 text-xs mt-1">
          {{ t('history.emptyHint') }}
        </p>
      </div>

      <ul v-else class="space-y-2">
        <li
          v-for="item in paginatedHistory"
          :key="item.id"
          class="surface rounded-2xl p-3 sm:p-4 flex items-center gap-3"
        >
          <div
            class="h-11 w-11 shrink-0 rounded-xl bg-primary/10 text-primary flex items-center justify-center overflow-hidden"
          >
            <img
              v-if="item.song?.cover_url"
              :src="item.song.cover_url"
              :alt="item.title"
              class="h-full w-full object-cover"
            />
            <Icon v-else icon="clarity:music-note-line" class="h-5 w-5" />
          </div>

          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5">
              <span class="text-sm font-semibold truncate">
                {{ item.title || t('common.unknownTrack') }}
              </span>
              <span :class="historyStatusClass(item)" class="shrink-0">
                {{ historyStatusLabel(item) }}
              </span>
            </div>
            <p class="text-xs text-base-content/60 truncate">
              {{ item.artists || t('common.unknownArtist') }}
            </p>
            <p class="text-xs text-base-content/40 truncate">
              {{ formatDate(item.updated_at) }}
              <span v-if="item.error">- {{ item.error }}</span>
            </p>
          </div>

          <div class="flex items-center gap-1 shrink-0">
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

      <nav
        v-if="historyPages > 1"
        class="mt-6 flex items-center justify-center gap-1 flex-wrap"
      >
        <button
          class="icon-btn"
          :disabled="historyPage === 1"
          @click="historyPage--"
          :title="t('common.previousPage')"
        >
          <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-[-90deg]" />
        </button>
        <button
          v-for="page in historyPages"
          :key="page"
          class="h-10 min-w-[2.5rem] rounded-full px-3 text-sm font-medium transition-colors"
          :class="
            page === historyPage
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/70 hover:text-base-content hover:bg-white/10'
          "
          @click="historyPage = page"
        >
          {{ page }}
        </button>
        <button
          class="icon-btn"
          :disabled="historyPage === historyPages"
          @click="historyPage++"
          :title="t('common.nextPage')"
        >
          <Icon icon="clarity:angle-line" class="h-4 w-4 rotate-90" />
        </button>
      </nav>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Icon } from '@iconify/vue'
import API from '../model/api'
import { useProgressTracker, useDownloadManager } from '../model/download'
import { useDownloadDestination } from '../model/downloadDestination'
import { useI18n } from '../i18n'

const PAGE_SIZE = 10

const pt = useProgressTracker()
const dm = useDownloadManager()
const dd = useDownloadDestination()
const { t } = useI18n()
const history = ref([])
const historyLoading = ref(false)
const historyError = ref('')
const historyPage = ref(1)
const retrying = ref({})

async function onClearAll() {
  if (!confirm(t('queue.clearAllPrompt'))) return
  await dm.clearAll()
}

const currentPage = ref(1)

const totalPages = computed(() =>
  Math.ceil(pt.downloadQueue.value.length / PAGE_SIZE)
)

const paginatedQueue = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return pt.downloadQueue.value.slice(start, start + PAGE_SIZE)
})

const historyPages = computed(() => Math.ceil(history.value.length / PAGE_SIZE))

const paginatedHistory = computed(() => {
  const start = (historyPage.value - 1) * PAGE_SIZE
  return history.value.slice(start, start + PAGE_SIZE)
})

watch(
  () => pt.downloadQueue.value.length,
  () => {
    if (currentPage.value > totalPages.value && totalPages.value > 0) {
      currentPage.value = totalPages.value
    }
  }
)

watch(
  () => history.value.length,
  () => {
    if (historyPage.value > historyPages.value && historyPages.value > 0) {
      historyPage.value = historyPages.value
    }
  }
)

watch(
  () => pt.historyRevision.value,
  () => {
    refreshHistory()
  }
)

onMounted(refreshHistory)

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
  if (item.status === 'downloading') return t('history.downloading')
  return t('history.queued')
}

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
  historyLoading.value = true
  historyError.value = ''
  try {
    const res = await API.getHistory()
    history.value = Array.isArray(res.data) ? res.data : []
  } catch {
    historyError.value = t('history.failedLoad')
  } finally {
    historyLoading.value = false
  }
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
</script>
