<template>
  <div class="min-h-0 overflow-x-hidden">
    <Navbar />

    <main class="mx-auto max-w-5xl w-full min-w-0 px-4 py-4 sm:py-8 sm:px-6 overflow-x-hidden">
      <div class="mb-6 sm:mb-8 mobile-page-header">
        <h1 class="text-2xl font-bold tracking-tight">
          {{ t('health.title') }}
        </h1>
        <p class="mt-1 text-sm text-base-content/60">
          {{ t('health.subtitle') }}
        </p>
      </div>

      <ServerConnectionPrompt class="mb-4" />

      <div
        v-if="error"
        class="surface rounded-2xl p-4 mb-4 flex gap-3 items-center text-sm text-error"
      >
        <Icon icon="clarity:exclamation-circle-line" class="h-5 w-5 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <div v-if="loading && !health" class="grid gap-4 md:grid-cols-2">
        <div v-for="n in 6" :key="n" class="skeleton h-32 rounded-2xl" />
      </div>

      <div
        v-else-if="!needsServerConnection() && health"
        class="space-y-4 sm:space-y-6 min-w-0"
      >
        <section class="surface health-card rounded-2xl p-4 sm:p-5 min-w-0 overflow-hidden">
          <div class="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
            <div class="flex min-w-0 items-center gap-3">
              <span
                class="inline-flex h-11 w-11 items-center justify-center rounded-xl"
                :class="
                  health.status === 'ok'
                    ? 'bg-primary/10 text-primary'
                    : 'bg-warning/10 text-warning'
                "
              >
                <Icon
                  :icon="
                    health.status === 'ok'
                      ? 'clarity:check-circle-line'
                      : 'clarity:exclamation-circle-line'
                  "
                  class="h-6 w-6"
                />
              </span>
              <div>
                <p class="text-sm font-semibold">
                  {{
                    health.status === 'ok'
                      ? t('health.statusOk')
                      : t('health.statusAttention')
                  }}
                </p>
                <p class="text-xs text-base-content/50">
                  {{ t('health.version', { version: health.version }) }}
                </p>
              </div>
            </div>
            <div class="flex min-w-0 flex-wrap gap-2 text-xs">
              <span class="pill bg-white/5 border border-white/10">
                Python {{ health.python }}
              </span>
              <span class="pill bg-white/5 border border-white/10">
                {{ t('health.queueTotal', { count: health.queue.total }) }}
              </span>
              <span class="pill badge-soft">
                {{
                  t('health.completed24h', {
                    count: health.history.completed_24h,
                  })
                }}
              </span>
              <span
                class="pill border"
                :class="
                  health.history.recent_failures > 0
                    ? 'badge-error-soft'
                    : 'badge-soft'
                "
              >
                {{
                  t('health.recentFailures', {
                    count: health.history.recent_failures,
                  })
                }}
              </span>
            </div>
          </div>
        </section>

        <section class="grid min-w-0 gap-4 md:grid-cols-2">
          <div class="surface health-card rounded-2xl p-4 sm:p-5 min-w-0 overflow-hidden">
            <div class="mb-4 flex items-center justify-between gap-3">
              <h2 class="text-sm font-semibold uppercase text-base-content/50">
                {{ t('health.downloads') }}
              </h2>
              <Icon icon="clarity:download-line" class="h-5 w-5 shrink-0 text-primary" />
            </div>
            <p class="text-xs text-base-content/40">
              {{ downloadLocationLabel }}
            </p>
            <p class="mt-1 break-all text-sm font-medium leading-snug">
              {{ displayedDownloadPath }}
            </p>
            <div class="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
              <div
                class="h-full bg-primary"
                :style="`width: ${health.downloads.disk.percent_used}%`"
              />
            </div>
            <div class="health-stat-grid mt-3">
              <div class="health-stat-item">
                <p class="text-base-content/40">{{ t('health.audioFiles') }}</p>
                <p class="font-semibold">{{ health.downloads.audio_count }}</p>
              </div>
              <div class="health-stat-item">
                <p class="text-base-content/40">{{ t('health.librarySize') }}</p>
                <p class="font-semibold">
                  {{ formatBytes(health.downloads.size_bytes) }}
                </p>
              </div>
              <div class="health-stat-item">
                <p class="text-base-content/40">{{ t('health.free') }}</p>
                <p class="font-semibold">
                  {{ formatBytes(health.downloads.disk.free_bytes) }}
                </p>
              </div>
            </div>
          </div>

          <div class="surface health-card rounded-2xl p-4 sm:p-5 min-w-0 overflow-hidden">
            <div class="mb-4 flex items-center justify-between gap-3">
              <h2 class="text-sm font-semibold uppercase text-base-content/50">
                {{ t('health.data') }}
              </h2>
              <Icon icon="clarity:folder-line" class="h-5 w-5 shrink-0 text-primary" />
            </div>
            <p class="break-all text-sm font-medium leading-snug">
              {{ health.data.path }}
            </p>
            <div class="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
              <div
                class="h-full bg-primary"
                :style="`width: ${health.data.disk.percent_used}%`"
              />
            </div>
            <div class="health-stat-grid mt-3">
              <div class="health-stat-item">
                <p class="text-base-content/40">{{ t('health.files') }}</p>
                <p class="font-semibold">{{ health.data.file_count }}</p>
              </div>
              <div class="health-stat-item">
                <p class="text-base-content/40">{{ t('health.dataSize') }}</p>
                <p class="font-semibold">
                  {{ formatBytes(health.data.size_bytes) }}
                </p>
              </div>
              <div class="health-stat-item">
                <p class="text-base-content/40">{{ t('health.used') }}</p>
                <p class="font-semibold">
                  {{ health.data.disk.percent_used }}%
                </p>
              </div>
            </div>
          </div>
        </section>

        <section class="grid min-w-0 gap-4 lg:grid-cols-[1fr_1fr]">
          <div class="surface health-card rounded-2xl p-4 sm:p-5 min-w-0 overflow-hidden">
            <h2 class="mb-4 text-sm font-semibold uppercase text-base-content/50">
              {{ t('health.tools') }}
            </h2>
            <ul class="space-y-3">
              <li
                v-for="tool in toolRows"
                :key="tool.name"
                class="flex items-center justify-between gap-4"
              >
                <div class="min-w-0">
                  <p class="text-sm font-medium">{{ tool.name }}</p>
                  <p class="break-all text-xs text-base-content/40 sm:truncate">
                    {{ tool.version || tool.path || t('health.notDetected') }}
                  </p>
                </div>
                <span
                  class="pill shrink-0"
                  :class="tool.available ? 'badge-soft' : 'badge-error-soft'"
                >
                  {{
                    tool.available
                      ? t('health.available')
                      : t('health.missing')
                  }}
                </span>
              </li>
            </ul>
          </div>

          <div class="surface health-card rounded-2xl p-4 sm:p-5 min-w-0 overflow-hidden">
            <h2 class="mb-4 text-sm font-semibold uppercase text-base-content/50">
              {{ t('health.settings') }}
            </h2>
            <ul class="health-settings-list">
              <li
                v-for="item in settingRows"
                :key="item.label"
                class="health-settings-row"
              >
                <span class="health-settings-label">{{ item.label }}</span>
                <span
                  class="health-settings-value"
                  :class="
                    isToggleValue(item.value)
                      ? item.value === t('common.yes')
                        ? 'badge-soft'
                        : 'badge-neutral-soft'
                      : ''
                  "
                >
                  {{ item.value }}
                </span>
              </li>
            </ul>
          </div>
        </section>

        <section class="surface health-card rounded-2xl p-4 sm:p-5 min-w-0 overflow-hidden">
          <div class="mb-4 flex items-center justify-between gap-3">
            <h2 class="text-sm font-semibold uppercase text-base-content/50">
              {{ t('health.recentHistory') }}
            </h2>
            <span class="text-xs text-base-content/40">
              {{ t('health.latestFive') }}
            </span>
          </div>
          <div
            v-if="health.history.recent.length === 0"
            class="py-8 text-center text-sm text-base-content/50"
          >
            {{ t('health.noHistory') }}
          </div>
          <ul v-else class="space-y-2">
            <li
              v-for="item in health.history.recent"
              :key="item.id"
              class="flex items-center justify-between gap-3 rounded-xl bg-white/5 px-3 py-2"
            >
              <div class="min-w-0">
                <p class="truncate text-sm font-medium">
                  {{ item.title || t('common.unknownTrack') }}
                </p>
                <p class="truncate text-xs text-base-content/50">
                  {{ item.artists || t('common.unknownArtist') }}
                </p>
              </div>
              <span class="pill shrink-0" :class="historyClass(item.status)">
                {{ historyLabel(item.status) }}
              </span>
            </li>
          </ul>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import API, { isHealthPayload } from '../model/api'
import Navbar from '../components/Navbar.vue'
import ServerConnectionPrompt from '../components/ServerConnectionPrompt.vue'
import { useDownloadDestination } from '../model/downloadDestination'
import { useHealthRefresh } from '../model/healthRefresh'
import { useI18n } from '../i18n'
import { needsServerConnection } from '../model/serverConnection'

const { t } = useI18n()
const downloadDestination = useDownloadDestination()
const healthRefresh = useHealthRefresh()
const health = ref(null)
const loading = ref(false)
const error = ref('')

const toolRows = computed(() => {
  if (!health.value) return []
  return [
    { name: 'ffmpeg', ...health.value.tools.ffmpeg },
    { name: 'yt-dlp', ...health.value.tools.yt_dlp },
  ]
})

const settingRows = computed(() => {
  if (!health.value) return []
  const settings = health.value.settings
  return [
    { label: t('settings.format'), value: settings.format },
    { label: t('settings.quality'), value: settings.bitrate },
    {
      label: t('settings.parallelDownloads'),
      value: settings.max_parallel_downloads,
    },
    { label: t('settings.generateM3u'), value: yesNo(settings.generate_m3u) },
    {
      label: t('settings.downloadLyrics'),
      value: yesNo(settings.download_lyrics),
    },
    {
      label: t('settings.enhanceMetadata'),
      value: yesNo(settings.enhance_metadata),
    },
    {
      label: t('settings.organizeByArtist'),
      value: yesNo(settings.organize_by_artist),
    },
    {
      label: t('settings.organizeByAlbum'),
      value: yesNo(settings.organize_by_album),
    },
  ]
})

const downloadLocationLabel = computed(() => {
  if (downloadDestination.isLocal.value) {
    return t('health.localDownloadLocation')
  }
  if (health.value?.downloads?.external_path) {
    return t('health.mediaSaveLocation')
  }
  return t('health.containerDownloadLocation')
})

const displayedDownloadPath = computed(() => {
  if (downloadDestination.isLocal.value) {
    return (
      downloadDestination.localFolderName.value ||
      t('settings.downloadDestinationLocal')
    )
  }
  return health.value?.downloads?.external_path || health.value?.downloads?.path
})

onMounted(() => {
  healthRefresh.register(loadHealth)
  loadHealth()
})

onUnmounted(() => {
  healthRefresh.unregister()
})

async function loadHealth() {
  if (needsServerConnection()) {
    health.value = null
    error.value = ''
    loading.value = false
    healthRefresh.setLoading(false)
    return
  }

  loading.value = true
  healthRefresh.setLoading(true)
  error.value = ''
  try {
    const res = await API.getHealth()
    if (!isHealthPayload(res.data)) {
      throw new Error('invalid health payload')
    }
    health.value = res.data
  } catch {
    health.value = null
    error.value = t('health.failedLoad')
  } finally {
    loading.value = false
    healthRefresh.setLoading(false)
  }
}

function formatBytes(value) {
  const bytes = Number(value || 0)
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB', 'TB']
  let size = bytes / 1024
  let index = 0
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024
    index += 1
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[index]}`
}

function yesNo(value) {
  return value ? t('common.yes') : t('common.no')
}

function isToggleValue(value) {
  return value === t('common.yes') || value === t('common.no')
}

function historyClass(status) {
  if (status === 'error') return 'badge-error-soft'
  if (status === 'done' || status === 'skipped') return 'badge-soft'
  return 'badge-neutral-soft'
}

function historyLabel(status) {
  if (status === 'error') return t('history.failed')
  if (status === 'skipped') return t('history.skipped')
  if (status === 'done') return t('history.done')
  if (status === 'downloading') return t('history.downloading')
  return t('history.queued')
}
</script>
