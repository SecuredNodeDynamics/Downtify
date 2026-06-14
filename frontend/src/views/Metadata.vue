<template>
  <div class="min-h-screen">
    <Navbar />
    <Settings />

    <main class="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div class="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">
            {{ t('metadata.title') }}
          </h1>
          <p class="mt-1 text-sm text-base-content/60">
            {{ t('metadata.subtitle') }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <select
            v-model.number="scanLimit"
            class="select h-11 rounded-full border-white/10 bg-base-100/85 text-sm"
            :disabled="loading"
            :title="t('metadata.resultLimit')"
          >
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
          <button
            class="btn btn-primary btn-sm h-11 rounded-full px-5"
            :disabled="loading"
            @click="scan"
          >
            <span
              v-if="loading"
              class="loading loading-spinner loading-xs mr-2"
            />
            <Icon v-else icon="clarity:refresh-line" class="h-4 w-4 mr-2" />
            {{ t('metadata.scan') }}
          </button>
          <button
            class="btn btn-sm h-11 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
            :disabled="
              loading ||
              activeTab !== 'needs' ||
              items.length === 0 ||
              repairingAll
            "
            @click="repairAll"
          >
            <span
              v-if="repairingAll"
              class="loading loading-spinner loading-xs mr-2"
            />
            <Icon v-else icon="clarity:check-circle-line" class="h-4 w-4 mr-2" />
            {{ t('metadata.repairAll') }}
          </button>
        </div>
      </div>

      <div
        v-if="error"
        class="surface mb-4 flex items-center gap-3 rounded-2xl p-4 text-sm text-error"
      >
        <Icon icon="clarity:exclamation-circle-line" class="h-5 w-5" />
        <span>{{ error }}</span>
      </div>

      <section class="mb-5 grid gap-3 sm:grid-cols-3">
        <div class="surface rounded-2xl p-4">
          <p class="text-xs uppercase text-base-content/40">
            {{ t('metadata.scanned') }}
          </p>
          <p class="mt-1 text-2xl font-semibold">{{ summary.scanned }}</p>
        </div>
        <div class="surface rounded-2xl p-4">
          <p class="text-xs uppercase text-base-content/40">
            {{ t('metadata.needsFix') }}
          </p>
          <p class="mt-1 text-2xl font-semibold text-primary">
            {{ summary.matched }}
          </p>
        </div>
        <div class="surface rounded-2xl p-4">
          <p class="text-xs uppercase text-base-content/40">
            {{ t('metadata.total') }}
          </p>
          <p class="mt-1 text-2xl font-semibold">{{ summary.total }}</p>
        </div>
      </section>

      <p class="mb-5 text-xs text-base-content/45">
        {{ t('metadata.serverOnly') }}
      </p>

      <div
        class="mb-5 inline-flex rounded-full border border-white/10 bg-base-100/75 p-1"
      >
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
          :class="
            activeTab === 'needs'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeTab = 'needs'"
        >
          {{ t('metadata.needsFix') }}
          <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
            {{ items.length }}
          </span>
        </button>
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
          :class="
            activeTab === 'completed'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeTab = 'completed'"
        >
          {{ t('metadata.completed') }}
          <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
            {{ completedItems.length }}
          </span>
        </button>
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
          :class="
            activeTab === 'clean'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeTab = 'clean'"
        >
          {{ t('metadata.clean') }}
          <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
            {{ cleanItems.length }}
          </span>
        </button>
      </div>

      <div class="max-h-[45rem] overflow-y-auto pr-2">
        <div v-if="loading && visibleItems.length === 0" class="space-y-3">
          <div v-for="n in 5" :key="n" class="skeleton h-24 rounded-2xl" />
        </div>

        <div
          v-else-if="visibleItems.length === 0"
          class="surface rounded-2xl p-10 text-center"
        >
          <Icon
            icon="clarity:tag-line"
            class="mx-auto mb-3 h-10 w-10 text-base-content/20"
          />
          <p class="text-sm text-base-content/50">
            {{ loading ? t('metadata.scanning') : t('metadata.empty') }}
          </p>
        </div>

        <ul v-else class="space-y-3">
          <li
            v-for="item in visibleItems"
            :key="item.file"
            class="surface rounded-2xl p-4 transition-all duration-300"
            :class="
              applying[item.file]
                ? 'scale-[1.01] border-primary/40 shadow-glow-sm'
                : ''
            "
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-semibold">{{ item.file }}</p>
                <p class="mt-1 text-xs text-base-content/45">
                  {{ displaySong(item.current) }}
                </p>
              </div>
              <span
                class="pill shrink-0"
                :class="
                  activeTab === 'completed'
                    ? 'badge-soft'
                    : activeTab === 'clean'
                      ? 'bg-white/5 text-base-content/50'
                    : 'bg-warning/10 text-warning'
                "
              >
                {{
                  activeTab === 'completed'
                    ? t('metadata.fixed')
                    : activeTab === 'clean'
                      ? t('metadata.clean')
                    : t('metadata.needsFix')
                }}
              </span>
            </div>

            <div
              class="mt-4 rounded-xl border border-white/10 bg-base-100/70 p-3"
            >
              <p class="text-xs font-semibold text-primary">
                {{ displaySong(item.candidate) }}
              </p>
              <div
                v-if="item.changes.length"
                class="mt-3 grid gap-2 text-xs sm:grid-cols-2"
              >
                <div
                  v-for="change in item.changes"
                  :key="`${item.file}-${change.field}`"
                  class="rounded-lg bg-white/5 p-2"
                >
                  <p class="font-semibold text-base-content/70">
                    {{ change.label }}
                  </p>
                  <p class="truncate text-base-content/40">
                    {{ change.before || t('metadata.blank') }}
                  </p>
                  <p class="truncate text-primary">
                    {{ change.after || t('metadata.blank') }}
                  </p>
                </div>
              </div>
              <p v-else class="mt-2 text-xs text-base-content/45">
                {{ t('metadata.idsOnly') }}
              </p>
            </div>

            <div v-if="activeTab === 'needs'" class="mt-4 flex justify-end">
              <button
                class="btn btn-sm h-10 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
                :class="fixed[item.file] ? 'text-primary' : ''"
                :disabled="applying[item.file] || fixed[item.file]"
                @click="apply(item)"
              >
                <span
                  v-if="applying[item.file]"
                  class="loading loading-spinner loading-xs mr-2"
                />
                <Icon
                  v-else
                  icon="clarity:check-line"
                  class="h-4 w-4 mr-2"
                />
                {{
                  applying[item.file]
                    ? t('metadata.fixing')
                    : fixed[item.file]
                      ? t('metadata.fixed')
                      : t('metadata.apply')
                }}
              </button>
            </div>
          </li>
        </ul>
      </div>

      <section class="mt-10 border-t border-white/10 pt-8">
        <div class="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 class="text-xl font-bold tracking-tight">
              {{ t('metadata.artistImages') }}
            </h2>
            <p class="mt-1 text-sm text-base-content/60">
              {{ t('metadata.artistImagesSubtitle') }}
            </p>
          </div>
          <div class="flex items-center gap-2">
            <select
              v-model.number="artistImageLimit"
              class="select h-11 rounded-full border-white/10 bg-base-100/85 text-sm"
              :disabled="artistImageLoading"
              :title="t('metadata.artistImageLimit')"
            >
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <button
              class="btn btn-primary btn-sm h-11 rounded-full px-5"
              :disabled="artistImageLoading"
              @click="scanArtistImages"
            >
              <span
                v-if="artistImageLoading"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:image-gallery-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanArtistImages') }}
            </button>
            <button
              class="btn btn-sm h-11 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="
                artistImageLoading ||
                artistImageItems.length === 0 ||
                repairingAllImages
              "
              @click="repairAllArtistImages"
            >
              <span
                v-if="repairingAllImages"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:check-circle-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.repairAll') }}
            </button>
          </div>
        </div>

        <div
          v-if="artistImageError"
          class="surface mb-4 flex items-center gap-3 rounded-2xl p-4 text-sm text-error"
        >
          <Icon icon="clarity:exclamation-circle-line" class="h-5 w-5" />
          <span>{{ artistImageError }}</span>
        </div>

        <section class="mb-5 grid gap-3 sm:grid-cols-3">
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.scanned') }}
            </p>
            <p class="mt-1 text-2xl font-semibold">
              {{ artistImageSummary.scanned }}
            </p>
          </div>
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.missingImages') }}
            </p>
            <p class="mt-1 text-2xl font-semibold text-primary">
              {{ artistImageItems.length }}
            </p>
          </div>
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.completed') }}
            </p>
            <p class="mt-1 text-2xl font-semibold">
              {{ completedArtistImages.length }}
            </p>
          </div>
        </section>

        <div class="max-h-[34rem] overflow-y-auto pr-2">
          <div
            v-if="artistImageLoading && artistImageItems.length === 0"
            class="space-y-3"
          >
            <div v-for="n in 4" :key="n" class="skeleton h-20 rounded-2xl" />
          </div>

          <div
            v-else-if="artistImageItems.length === 0"
            class="surface rounded-2xl p-10 text-center"
          >
            <Icon
              icon="clarity:image-gallery-line"
              class="mx-auto mb-3 h-10 w-10 text-base-content/20"
            />
            <p class="text-sm text-base-content/50">
              {{
                artistImageLoading
                  ? t('metadata.scanning')
                  : t('metadata.emptyArtistImages')
              }}
            </p>
          </div>

          <ul v-else class="space-y-3">
            <li
              v-for="item in artistImageItems"
              :key="`${item.artist_id}-${item.folder}`"
              class="surface rounded-2xl p-4"
              :class="
                applyingArtistImages[itemKey(item)]
                  ? 'scale-[1.01] border-primary/40 shadow-glow-sm'
                  : ''
              "
            >
              <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_auto_auto] md:items-center">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold">
                    {{ item.artist }}
                  </p>
                  <p class="mt-1 text-xs text-base-content/45">
                    {{ item.target || item.folder }}
                  </p>
                  <p class="mt-1 text-xs text-primary">
                    {{ item.source }}
                  </p>
                </div>
                <div class="grid grid-cols-[5rem_5rem] items-center gap-3 justify-self-center">
                  <div>
                    <p class="mb-1 text-center text-[0.65rem] uppercase text-base-content/40">
                      {{ t('metadata.before') }}
                    </p>
                    <div
                      class="flex aspect-square w-20 items-center justify-center rounded-xl border border-white/10 bg-base-100/80"
                    >
                      <Icon
                        icon="clarity:user-line"
                        class="h-9 w-9 text-base-content/35"
                      />
                    </div>
                  </div>
                  <div>
                    <p class="mb-1 text-center text-[0.65rem] uppercase text-base-content/40">
                      {{ t('metadata.after') }}
                    </p>
                    <div
                      class="aspect-square w-20 overflow-hidden rounded-xl border border-primary/30 bg-base-100/80"
                    >
                      <img
                        v-if="item.preview_url"
                        :src="item.preview_url"
                        :alt="item.artist"
                        class="h-full w-full object-cover"
                        loading="lazy"
                      />
                      <div
                        v-else
                        class="flex h-full w-full items-center justify-center"
                      >
                        <Icon
                          icon="clarity:image-gallery-line"
                          class="h-9 w-9 text-base-content/35"
                        />
                      </div>
                    </div>
                  </div>
                </div>
                <button
                  class="btn btn-sm h-10 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
                  :class="fixedArtistImages[itemKey(item)] ? 'text-primary' : ''"
                  :disabled="
                    applyingArtistImages[itemKey(item)] ||
                    fixedArtistImages[itemKey(item)]
                  "
                  @click="applyArtistImage(item)"
                >
                  <span
                    v-if="applyingArtistImages[itemKey(item)]"
                    class="loading loading-spinner loading-xs mr-2"
                  />
                  <Icon v-else icon="clarity:check-line" class="h-4 w-4 mr-2" />
                  {{
                    applyingArtistImages[itemKey(item)]
                      ? t('metadata.fixing')
                      : fixedArtistImages[itemKey(item)]
                        ? t('metadata.fixed')
                        : t('metadata.apply')
                  }}
                </button>
              </div>
            </li>
          </ul>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Icon } from '@iconify/vue'

import Navbar from '/src/components/Navbar.vue'
import Settings from '/src/components/Settings.vue'
import API from '/src/model/api'
import { useI18n } from '/src/i18n'

const { t } = useI18n()
const loading = ref(false)
const error = ref('')
const items = ref([])
const cleanItems = ref([])
const applying = ref({})
const fixed = ref({})
const completedItems = ref([])
const activeTab = ref('needs')
const repairingAll = ref(false)
const scanLimit = ref(25)
const summary = ref({ scanned: 0, matched: 0, total: 0 })
const artistImageLoading = ref(false)
const artistImageError = ref('')
const artistImageLimit = ref(50)
const artistImageItems = ref([])
const completedArtistImages = ref([])
const applyingArtistImages = ref({})
const fixedArtistImages = ref({})
const repairingAllImages = ref(false)
const artistImageSummary = ref({ scanned: 0, matched: 0, total: 0 })
let pollTimer = null
let artistImagePollTimer = null

const visibleItems = computed(() =>
  activeTab.value === 'completed'
    ? completedItems.value
    : activeTab.value === 'clean'
      ? cleanItems.value
      : items.value
)

function displaySong(song) {
  const artists = (song?.artists || []).join(', ')
  const title = song?.name || t('common.unknownTrack')
  const album = song?.album_name ? ` - ${song.album_name}` : ''
  return `${artists || t('common.unknownArtist')} - ${title}${album}`
}

function itemKey(item) {
  return `${item.artist_id}-${item.folder}`
}

function applyScanStatus(data) {
  loading.value = data.status === 'scanning'
  scanLimit.value = data.limit || scanLimit.value
  summary.value = {
    scanned: data.scanned || 0,
    matched: data.matched || 0,
    total: data.total || 0,
  }
  items.value = data.items || []
  cleanItems.value = data.clean || cleanItems.value
  completedItems.value = data.completed || completedItems.value
  if (data.status === 'error') {
    error.value = data.error || t('metadata.failedScan')
  }
}

function applyArtistImageStatus(data) {
  artistImageLoading.value = data.status === 'scanning'
  artistImageLimit.value = data.limit || artistImageLimit.value
  artistImageSummary.value = {
    scanned: data.scanned || 0,
    matched: data.matched || 0,
    total: data.total || 0,
  }
  artistImageItems.value = data.items || []
  completedArtistImages.value =
    data.completed || completedArtistImages.value
  if (data.status === 'error') {
    artistImageError.value = data.error || t('metadata.failedArtistImageScan')
  }
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function stopArtistImagePolling() {
  if (artistImagePollTimer !== null) {
    clearInterval(artistImagePollTimer)
    artistImagePollTimer = null
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(refreshScanStatus, 2000)
}

function startArtistImagePolling() {
  stopArtistImagePolling()
  artistImagePollTimer = setInterval(refreshArtistImageStatus, 1500)
}

async function refreshScanStatus() {
  try {
    const res = await API.getMetadataScanStatus()
    applyScanStatus(res.data)
    if (res.data.status !== 'scanning') {
      stopPolling()
    }
  } catch {
    stopPolling()
    loading.value = false
    error.value = t('metadata.failedScan')
  }
}

async function refreshArtistImageStatus() {
  try {
    const res = await API.getArtistImageScanStatus()
    applyArtistImageStatus(res.data)
    if (res.data.status !== 'scanning') {
      stopArtistImagePolling()
    }
  } catch {
    stopArtistImagePolling()
    artistImageLoading.value = false
    artistImageError.value = t('metadata.failedArtistImageScan')
  }
}

async function scan() {
  loading.value = true
  error.value = ''
  fixed.value = {}
  try {
    const res = await API.startMetadataScan(scanLimit.value)
    applyScanStatus(res.data)
    if (res.data.status === 'scanning') {
      startPolling()
    }
  } catch {
    error.value = t('metadata.failedScan')
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await API.getMetadataScanStatus()
    applyScanStatus(res.data)
    if (res.data.status === 'scanning') {
      startPolling()
    }
  } catch {
    // The page can still start a fresh scan if status lookup fails.
  }
  try {
    const res = await API.getArtistImageScanStatus()
    applyArtistImageStatus(res.data)
    if (res.data.status === 'scanning') {
      startArtistImagePolling()
    }
  } catch {
    // The page can still start a fresh artist image scan.
  }
})

onBeforeUnmount(() => {
  stopPolling()
  stopArtistImagePolling()
})

async function apply(item) {
  applying.value = { ...applying.value, [item.file]: true }
  error.value = ''
  try {
    const res = await API.applyMetadata(item.file)
    const remainingChanges = res.data?.changes || []
    if (remainingChanges.length === 0) {
      fixed.value = { ...fixed.value, [item.file]: true }
      completedItems.value = [res.data, ...completedItems.value]
      items.value = items.value.filter((existing) => existing.file !== item.file)
      summary.value = {
        ...summary.value,
        matched: Math.max(0, summary.value.matched - 1),
      }
    } else {
      error.value = t('metadata.failedVerify')
    }
    if (remainingChanges.length > 0) {
      items.value = items.value.map((existing) =>
        existing.file === item.file
          ? {
              ...existing,
              current: res.data.current || existing.current,
              changes: remainingChanges,
            }
          : existing
      )
    }
  } catch (err) {
    const detail = err?.response?.data?.detail
    error.value = detail
      ? `${t('metadata.failedApply')} ${detail}`
      : t('metadata.failedApply')
  } finally {
    applying.value = { ...applying.value, [item.file]: false }
  }
}

async function repairAll() {
  repairingAll.value = true
  for (const item of [...items.value]) {
    // eslint-disable-next-line no-await-in-loop
    await apply(item)
  }
  repairingAll.value = false
}

async function scanArtistImages() {
  artistImageLoading.value = true
  artistImageError.value = ''
  fixedArtistImages.value = {}
  try {
    const res = await API.scanArtistImages(artistImageLimit.value)
    applyArtistImageStatus(res.data)
    if (res.data.status === 'scanning') {
      startArtistImagePolling()
    }
  } catch {
    artistImageError.value = t('metadata.failedArtistImageScan')
    artistImageLoading.value = false
  }
}

async function applyArtistImage(item) {
  const key = itemKey(item)
  applyingArtistImages.value = {
    ...applyingArtistImages.value,
    [key]: true,
  }
  artistImageError.value = ''
  try {
    const res = await API.applyArtistImage(item)
    if ((res.data?.saved || []).length === 0) {
      artistImageError.value = t('metadata.failedArtistImageApply')
      return
    }
    fixedArtistImages.value = { ...fixedArtistImages.value, [key]: true }
    completedArtistImages.value = [res.data, ...completedArtistImages.value]
    artistImageItems.value = artistImageItems.value.filter(
      (existing) => itemKey(existing) !== key
    )
  } catch (err) {
    const detail = err?.response?.data?.detail
    artistImageError.value = detail
      ? `${t('metadata.failedArtistImageApply')} ${detail}`
      : t('metadata.failedArtistImageApply')
  } finally {
    applyingArtistImages.value = {
      ...applyingArtistImages.value,
      [key]: false,
    }
  }
}

async function repairAllArtistImages() {
  repairingAllImages.value = true
  for (const item of [...artistImageItems.value]) {
    // eslint-disable-next-line no-await-in-loop
    await applyArtistImage(item)
  }
  repairingAllImages.value = false
}
</script>
