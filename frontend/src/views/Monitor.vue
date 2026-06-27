<template>
  <div class="monitor-view">
    <Navbar />

    <div class="monitor-page">
      <!-- Header -->
      <div class="monitor-header mb-6 sm:mb-8 mobile-page-header">
        <h1 class="text-2xl font-bold tracking-tight">
          {{ t('monitor.title') }}
        </h1>
        <p class="mt-1 text-sm text-base-content/60">
          {{ t('monitor.subtitle') }}
        </p>
      </div>

      <!-- Add form -->
      <div
        class="monitor-add-panel surface rounded-2xl p-4 sm:p-5 mb-6 sm:mb-8 min-w-0 overflow-hidden"
      >
        <h2
          class="text-sm font-semibold uppercase tracking-wider text-base-content/50 mb-4"
        >
          {{ t('monitor.watchNew') }}
        </h2>
        <form @submit.prevent="onAdd" class="monitor-add-form space-y-3">
          <div class="grid grid-cols-2 gap-2">
            <button
              type="button"
              class="h-11 rounded-2xl border text-sm font-medium transition-colors"
              :class="
                newKind === 'playlist'
                  ? 'border-primary/60 bg-primary/15 text-primary'
                  : 'border-white/10 bg-base-100/60 text-base-content/70'
              "
              :disabled="adding"
              @click="newKind = 'playlist'"
            >
              {{ t('monitor.typePlaylist') }}
            </button>
            <button
              type="button"
              class="h-11 rounded-2xl border text-sm font-medium transition-colors"
              :class="
                newKind === 'artist'
                  ? 'border-primary/60 bg-primary/15 text-primary'
                  : 'border-white/10 bg-base-100/60 text-base-content/70'
              "
              :disabled="adding"
              @click="newKind = 'artist'"
            >
              {{ t('monitor.typeArtist') }}
            </button>
          </div>
          <div class="monitor-target-search relative min-w-0">
            <div class="relative">
              <Icon
                icon="clarity:search-line"
                class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-base-content/35"
              />
              <input
                v-model="newUrl"
                type="search"
                inputmode="search"
                autocapitalize="off"
                autocorrect="off"
                spellcheck="false"
                :placeholder="urlPlaceholder"
                class="input-modern input-modern-plain h-12 w-full min-w-0 pl-10 pr-10 text-base sm:text-sm"
                :disabled="adding"
              />
              <button
                v-if="newUrl"
                type="button"
                class="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-base-content/45 transition-colors hover:bg-white/10 hover:text-base-content"
                :title="t('monitor.clearSearch')"
                :disabled="adding"
                @click="clearTargetSearch"
              >
                <Icon icon="clarity:times-line" class="h-4 w-4" />
              </button>
            </div>

            <div
              v-if="selectedTarget"
              class="mt-2 flex items-center gap-2 rounded-2xl border border-primary/30 bg-primary/10 px-3 py-2 text-sm text-primary"
            >
              <CoverImage
                :src="resultCover(selectedTarget)"
                :alt="selectedTarget.name"
                img-class="h-9 w-9 shrink-0 rounded-xl object-cover border border-primary/20 bg-base-100/60"
              >
                <template #fallback>
                  <Icon
                    :icon="
                      newKind === 'artist'
                        ? 'clarity:user-line'
                        : 'clarity:music-note-line'
                    "
                    class="h-4 w-4 text-primary/70"
                  />
                </template>
              </CoverImage>
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium">{{ selectedTarget.name }}</p>
                <p class="truncate text-xs text-primary/70">
                  {{ selectedTarget.subtitle || t('monitor.selectedTarget') }}
                </p>
              </div>
              <Icon icon="clarity:check-circle-line" class="h-5 w-5 shrink-0" />
            </div>

            <div
              v-else-if="showTargetResults"
              class="monitor-search-results mt-2 overflow-hidden rounded-2xl border border-white/10 bg-base-100/95 shadow-2xl shadow-black/25"
            >
              <div
                v-if="targetSearchLoading"
                class="flex items-center gap-2 px-3 py-3 text-sm text-base-content/55"
              >
                <span class="loading loading-spinner loading-xs" />
                <span>{{ t('monitor.searching') }}</span>
              </div>
              <template v-else>
                <button
                  v-for="result in targetSearchResults"
                  :key="`${result.kind}:${result.spotify_id}`"
                  type="button"
                  class="flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-primary/10"
                  @click="selectTarget(result)"
                >
                  <CoverImage
                    :src="resultCover(result)"
                    :alt="result.name"
                    img-class="h-11 w-11 shrink-0 rounded-xl object-cover border border-white/10 bg-base-100/60"
                  >
                    <template #fallback>
                      <Icon
                        :icon="
                          newKind === 'artist'
                            ? 'clarity:user-line'
                            : 'clarity:music-note-line'
                        "
                        class="h-5 w-5 text-base-content/25"
                      />
                    </template>
                  </CoverImage>
                  <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-medium">{{ result.name }}</p>
                    <p class="truncate text-xs text-base-content/45">
                      {{ result.subtitle || t('monitor.selectTarget') }}
                    </p>
                  </div>
                  <Icon
                    icon="clarity:plus-circle-line"
                    class="h-5 w-5 shrink-0 text-primary"
                  />
                </button>
              </template>
              <p
                v-if="targetSearchError"
                class="px-3 py-3 text-sm text-error"
              >
                {{ targetSearchError }}
              </p>
              <p
                v-else-if="showNoTargetResults"
                class="px-3 py-3 text-sm text-base-content/45"
              >
                {{ t('monitor.noSearchResults') }}
              </p>
            </div>
          </div>
          <div class="flex flex-col gap-2 sm:flex-row sm:items-stretch">
            <select
              v-model="newInterval"
              class="select w-full sm:min-w-[10rem] sm:flex-1 rounded-2xl border border-white/10 bg-base-100/85 focus:border-primary/60 h-12 px-4 text-sm"
              :disabled="adding"
            >
              <option :value="15">{{ t('monitor.every15') }}</option>
              <option :value="30">{{ t('monitor.every30') }}</option>
              <option :value="60">{{ t('monitor.every1h') }}</option>
              <option :value="180">{{ t('monitor.every3h') }}</option>
              <option :value="360">{{ t('monitor.every6h') }}</option>
              <option :value="720">{{ t('monitor.every12h') }}</option>
              <option :value="1440">{{ t('monitor.every1d') }}</option>
              <option :value="10080">{{ t('monitor.every1w') }}</option>
              <option :value="20160">{{ t('monitor.every2w') }}</option>
              <option :value="43200">{{ t('monitor.every1mo') }}</option>
            </select>
            <button
              type="submit"
              class="btn btn-primary h-12 w-full sm:w-auto sm:shrink-0 px-6 rounded-2xl"
              :disabled="adding || !monitorTargetUrl"
            >
              <span v-if="adding" class="loading loading-spinner loading-xs" />
              <span v-else>{{ t('monitor.watch') }}</span>
            </button>
          </div>
        </form>
        <p v-if="addError" class="mt-2 text-xs text-error">{{ addError }}</p>
      </div>

      <!-- Monitored items -->
      <section
        class="monitor-list-panel surface rounded-2xl p-3 sm:p-4 mb-6 sm:mb-8 min-w-0"
      >
        <div
          class="mb-3 flex items-center justify-between gap-3 px-1 sm:px-0"
        >
          <div class="min-w-0">
            <h2
              class="text-sm font-semibold uppercase tracking-wider text-base-content/50"
            >
              {{
                newKind === 'artist'
                  ? t('monitor.kindArtist')
                  : t('monitor.kindPlaylist')
              }}
            </h2>
            <p class="mt-0.5 text-xs text-base-content/40">
              {{
                `${filteredPlaylists.length} ${
                  newKind === 'artist'
                    ? t('monitor.kindArtist')
                    : t('monitor.kindPlaylist')
                }`
              }}
            </p>
          </div>
          <button
            type="button"
            class="icon-btn h-10 w-10 shrink-0"
            :title="t('monitor.checkNow')"
            @click="load"
          >
            <Icon icon="clarity:refresh-line" class="h-4 w-4" />
          </button>
        </div>

        <div class="monitor-list-scroll">
          <div v-if="loading" class="grid gap-3 sm:grid-cols-2">
            <div v-for="n in 4" :key="n" class="skeleton h-56 rounded-2xl" />
          </div>

          <div
            v-else-if="loadError"
            class="rounded-2xl border border-error/20 bg-error/10 p-4 text-sm text-error flex items-center gap-3"
          >
            <Icon
              icon="clarity:exclamation-circle-line"
              class="h-5 w-5 shrink-0"
            />
            <span>{{ loadError }}</span>
          </div>

          <div
            v-else-if="filteredPlaylists.length === 0"
            class="rounded-2xl border border-white/10 bg-base-100/30 p-10 flex flex-col items-center text-center"
          >
            <Icon
              icon="clarity:music-note-line"
              class="h-12 w-12 text-base-content/20 mb-4"
            />
            <p class="text-base-content/50 text-sm">
              {{ t('monitor.empty') }}
            </p>
            <p class="text-base-content/40 text-xs mt-1">
              {{ t('monitor.emptyHint') }}
            </p>
          </div>

          <ul v-else class="monitor-card-grid">
            <li
              v-for="pl in filteredPlaylists"
              :key="pl.id"
              class="monitor-card rounded-2xl border border-white/10 bg-base-100/55 p-3 shadow-lg shadow-black/10"
            >
              <div class="flex gap-3 min-w-0 overflow-hidden">
                <CoverImage
                :src="coverForItem(pl).src"
                :fallbacks="coverForItem(pl).fallbacks"
                :alt="pl.name"
                img-class="monitor-card-cover h-20 w-20 rounded-2xl object-cover border border-white/10 bg-base-100/60"
                >
                  <template #fallback>
                    <Icon
                      :icon="
                        pl.kind === 'artist'
                          ? 'clarity:user-line'
                          : 'clarity:music-note-line'
                      "
                      class="h-7 w-7 text-base-content/25"
                    />
                  </template>
                </CoverImage>

                <div class="min-w-0 flex-1 overflow-hidden">
                  <div class="mb-1 flex items-start justify-between gap-2">
                    <h3
                      class="monitor-card-title text-sm font-semibold leading-snug"
                    >
                      {{ pl.name }}
                    </h3>
                    <span
                      class="pill shrink-0 text-xs"
                      :class="pl.enabled ? 'badge-soft' : 'badge-neutral-soft'"
                    >
                      {{
                        pl.enabled ? t('monitor.active') : t('monitor.paused')
                      }}
                    </span>
                  </div>
                  <div class="space-y-1 text-xs text-base-content/50">
                    <p class="flex items-center gap-1">
                      <Icon icon="clarity:refresh-line" class="h-3 w-3" />
                      <span>
                        {{
                          t('monitor.everyInterval', {
                            interval: formatInterval(pl.interval_minutes),
                          })
                        }}
                      </span>
                    </p>
                    <p class="flex items-center gap-1">
                      <Icon icon="clarity:music-note-line" class="h-3 w-3" />
                      <span>
                        {{
                          pl.last_track_count === 1
                            ? t('monitor.tracksOne', {
                                count: pl.last_track_count,
                              })
                            : t('monitor.tracksMany', {
                                count: pl.last_track_count,
                              })
                        }}
                      </span>
                    </p>
                    <p class="flex items-center gap-1">
                      <Icon icon="clarity:clock-line" class="h-3 w-3" />
                      <span v-if="pl.last_checked">
                        {{
                          t('monitor.checked', {
                            when: timeAgo(pl.last_checked),
                          })
                        }}
                      </span>
                      <span v-else class="italic">
                        {{ t('monitor.notChecked') }}
                      </span>
                    </p>
                  </div>
                </div>
              </div>

              <div class="mt-3 grid grid-cols-[1fr_auto] gap-2">
                <select
                  :value="draftInterval(pl)"
                  class="select select-sm h-11 min-w-0 rounded-xl border border-white/10 bg-base-100/80 text-sm focus:border-primary/60"
                  @change="onIntervalDraftChange(pl, $event)"
                >
                  <option :value="15">{{ t('monitor.short15') }}</option>
                  <option :value="30">{{ t('monitor.short30') }}</option>
                  <option :value="60">{{ t('monitor.short1h') }}</option>
                  <option :value="180">{{ t('monitor.short3h') }}</option>
                  <option :value="360">{{ t('monitor.short6h') }}</option>
                  <option :value="720">{{ t('monitor.short12h') }}</option>
                  <option :value="1440">{{ t('monitor.short1d') }}</option>
                  <option :value="10080">{{ t('monitor.short1w') }}</option>
                  <option :value="20160">{{ t('monitor.short2w') }}</option>
                  <option :value="43200">{{ t('monitor.short1mo') }}</option>
                </select>

                <button
                  type="button"
                  class="btn btn-sm h-11 rounded-xl px-4"
                  :class="
                    intervalDirty(pl)
                      ? 'btn-primary'
                      : 'border-white/10 bg-base-100/40 text-base-content/40'
                  "
                  :disabled="!intervalDirty(pl) || applyingInterval[pl.id]"
                  @click="onApplyInterval(pl)"
                >
                  <span
                    v-if="applyingInterval[pl.id]"
                    class="loading loading-spinner loading-xs"
                  />
                  <span v-else>{{ t('monitor.applyInterval') }}</span>
                </button>
              </div>

              <div class="mt-2 grid grid-cols-3 gap-2">
                <button
                  class="monitor-action-btn"
                  :class="{ 'monitor-action-btn-pause': pl.enabled }"
                  :title="pl.enabled ? t('monitor.pause') : t('monitor.resume')"
                  @click="onToggle(pl)"
                >
                <Icon
                  :icon="
                    pl.enabled ? 'clarity:pause-line' : 'clarity:play-line'
                  "
                  class="h-4 w-4"
                />
                </button>

                <button
                  class="monitor-action-btn"
                  :title="t('monitor.checkNow')"
                  :disabled="checking[pl.id]"
                  @click="onCheck(pl)"
                >
                  <span
                    v-if="checking[pl.id]"
                    class="loading loading-spinner loading-xs"
                  />
                  <Icon v-else icon="clarity:refresh-line" class="h-4 w-4" />
                </button>

                <button
                  class="monitor-action-btn monitor-action-btn-danger"
                  :title="t('monitor.stop')"
                  @click="onDelete(pl)"
              >
                  <Icon icon="clarity:trash-line" class="h-4 w-4" />
                </button>
              </div>
              <p
                v-if="intervalErrors[pl.id] || actionErrors[pl.id]"
                class="mt-2 text-[11px] leading-snug text-error"
              >
                {{ intervalErrors[pl.id] || actionErrors[pl.id] }}
              </p>
            </li>
          </ul>
        </div>
      </section>

      <!-- Info banner -->
      <div
        class="monitor-info mt-8 surface rounded-2xl p-4 flex gap-3 text-sm text-base-content/60"
      >
        <Icon
          icon="clarity:info-standard-line"
          class="h-5 w-5 shrink-0 mt-0.5 text-primary/70"
        />
        <p>{{ t('monitor.info') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Icon } from '@iconify/vue'
import Navbar from '/src/components/Navbar.vue'
import CoverImage from '/src/components/CoverImage.vue'
import monitorAPI from '/src/model/monitor.js'
import API from '/src/model/api.js'
import { removeMonitoredArtist } from '/src/model/monitoredArtists.js'
import { useI18n } from '/src/i18n'

const { t } = useI18n()

const playlists = ref([])
const loading = ref(false)
const loadError = ref('')
const adding = ref(false)
const addError = ref('')
const newUrl = ref('')
const newKind = ref('artist')
const newInterval = ref(60)
const selectedTarget = ref(null)
const targetSearchResults = ref([])
const targetSearchLoading = ref(false)
const targetSearchError = ref('')
let targetSearchTimer = 0
let targetSearchSeq = 0
const checking = ref({})
const applyingInterval = ref({})
const intervalDrafts = ref({})
const intervalErrors = ref({})
const actionErrors = ref({})

const urlPlaceholder = computed(() =>
  newKind.value === 'artist'
    ? t('monitor.urlPlaceholderArtist')
    : t('monitor.urlPlaceholderPlaylist')
)
const trimmedTargetQuery = computed(() => newUrl.value.trim())
const monitorTargetUrl = computed(() => {
  if (selectedTarget.value?.url) return selectedTarget.value.url
  return isSpotifyMonitorUrl(trimmedTargetQuery.value)
    ? trimmedTargetQuery.value
    : ''
})
const showNoTargetResults = computed(
  () =>
    trimmedTargetQuery.value.length >= 2 &&
    !isSpotifyMonitorUrl(trimmedTargetQuery.value) &&
    !targetSearchLoading.value &&
    !targetSearchError.value &&
    targetSearchResults.value.length === 0
)
const showTargetResults = computed(
  () =>
    targetSearchLoading.value ||
    targetSearchError.value ||
    targetSearchResults.value.length > 0 ||
    showNoTargetResults.value
)
const filteredPlaylists = computed(() =>
  playlists.value.filter((pl) => pl.kind === newKind.value)
)

function isSpotifyMonitorUrl(value) {
  return /^https?:\/\/open\.spotify\.com\/(artist|playlist)\//i.test(
    String(value || '').trim()
  )
}

function clearTargetSearch() {
  newUrl.value = ''
  selectedTarget.value = null
  targetSearchResults.value = []
  targetSearchError.value = ''
}

function selectTarget(result) {
  selectedTarget.value = result
  newUrl.value = result.name || ''
  targetSearchResults.value = []
  targetSearchError.value = ''
}

function resultCover(result) {
  const imageUrl = String(result?.image_url || '').trim()
  return imageUrl ? API.searchCoverUrl(imageUrl, 160) : ''
}

async function runTargetSearch(seq, query, kind) {
  targetSearchLoading.value = true
  targetSearchError.value = ''
  try {
    const res = await monitorAPI.searchMonitorTargets(query, kind, 6)
    if (seq !== targetSearchSeq) return
    targetSearchResults.value = res.data?.results || []
  } catch (err) {
    if (seq !== targetSearchSeq) return
    targetSearchResults.value = []
    targetSearchError.value =
      err?.response?.data?.detail || err?.message || t('monitor.searchFailed')
  } finally {
    if (seq === targetSearchSeq) {
      targetSearchLoading.value = false
    }
  }
}

watch(
  [trimmedTargetQuery, newKind],
  ([query, kind]) => {
    window.clearTimeout(targetSearchTimer)
    targetSearchSeq += 1
    targetSearchError.value = ''

    if (
      selectedTarget.value?.name === query &&
      selectedTarget.value?.kind === kind
    ) {
      targetSearchLoading.value = false
      targetSearchResults.value = []
      return
    }

    if (
      selectedTarget.value &&
      (selectedTarget.value.name !== query || selectedTarget.value.kind !== kind)
    ) {
      selectedTarget.value = null
    }

    if (query.length < 2 || isSpotifyMonitorUrl(query)) {
      targetSearchLoading.value = false
      targetSearchResults.value = []
      return
    }

    const seq = targetSearchSeq
    targetSearchTimer = window.setTimeout(() => {
      runTargetSearch(seq, query, kind)
    }, 300)
  },
  { flush: 'post' }
)

async function load() {
  loadError.value = ''
  if (!playlists.value.length) {
    loading.value = true
  }
  try {
    const res = await monitorAPI.listMonitoredPlaylists()
    setPlaylists(res.data || [])
    if (res.fromCache && res.refresh) {
      loading.value = false
      try {
        const fresh = await res.refresh
        setPlaylists(fresh.data || [])
      } catch {
        // Keep the cached list when the live refresh fails.
      }
      return
    }
  } catch (err) {
    loadError.value =
      err?.response?.data?.detail || err?.message || t('monitor.failedLoad')
  } finally {
    loading.value = false
  }
}

function setPlaylists(items) {
  playlists.value = items
  const drafts = {}
  const errors = {}
  const actions = {}
  for (const pl of items) {
    drafts[pl.id] = Number(pl.interval_minutes) || 60
    errors[pl.id] = ''
    actions[pl.id] = ''
  }
  intervalDrafts.value = drafts
  intervalErrors.value = errors
  actionErrors.value = actions
}

function draftInterval(pl) {
  const draft = intervalDrafts.value[pl.id]
  if (draft === undefined) return Number(pl.interval_minutes) || 60
  return Number(draft)
}

function onIntervalDraftChange(pl, event) {
  const val = Number.parseInt(String(event.target.value || ''), 10)
  if (!Number.isFinite(val)) return
  intervalDrafts.value = {
    ...intervalDrafts.value,
    [pl.id]: val,
  }
  intervalErrors.value = {
    ...intervalErrors.value,
    [pl.id]: '',
  }
}

function coverForItem(pl) {
  const spotifyUrl = String(pl?.image_url || '').trim()
  const remote = spotifyUrl ? API.searchCoverUrl(spotifyUrl, 320) : ''
  if (pl?.kind === 'artist') {
    const local = API.coverSourcesForArtist(pl.name)
    const fallbacks = [remote, spotifyUrl, local.src]
    fallbacks.push(...local.fallbacks)
    return {
      src: remote || spotifyUrl || local.src,
      fallbacks: [...new Set(fallbacks.filter(Boolean))],
    }
  }
  return {
    src: remote || spotifyUrl,
    fallbacks: [...new Set([spotifyUrl].filter(Boolean))],
  }
}

function intervalDirty(pl) {
  return draftInterval(pl) !== Number(pl.interval_minutes)
}

async function onAdd() {
  addError.value = ''
  adding.value = true
  try {
    const res = await monitorAPI.addMonitoredPlaylist(
      monitorTargetUrl.value,
      newInterval.value,
      newKind.value
    )
    setPlaylists([res.data, ...playlists.value])
    clearTargetSearch()
  } catch (e) {
    addError.value = e?.response?.data?.detail || t('monitor.failedAdd')
  } finally {
    adding.value = false
  }
}

async function onToggle(pl) {
  actionErrors.value = { ...actionErrors.value, [pl.id]: '' }
  try {
    const res = await monitorAPI.updateMonitoredPlaylist(pl.id, {
      enabled: !pl.enabled,
    })
    Object.assign(pl, res.data)
  } catch (err) {
    actionErrors.value = {
      ...actionErrors.value,
      [pl.id]: err?.response?.data?.detail || t('monitor.failedUpdate'),
    }
  }
}

async function onApplyInterval(pl) {
  const val = draftInterval(pl)
  if (!Number.isFinite(val) || val === Number(pl.interval_minutes)) return
  applyingInterval.value = { ...applyingInterval.value, [pl.id]: true }
  intervalErrors.value = { ...intervalErrors.value, [pl.id]: '' }
  actionErrors.value = { ...actionErrors.value, [pl.id]: '' }
  try {
    const res = await monitorAPI.updateMonitoredPlaylist(pl.id, {
      interval_minutes: val,
    })
    Object.assign(pl, res.data)
    intervalDrafts.value = {
      ...intervalDrafts.value,
      [pl.id]: Number(pl.interval_minutes),
    }
    intervalErrors.value = {
      ...intervalErrors.value,
      [pl.id]: '',
    }
  } catch (err) {
    intervalDrafts.value = {
      ...intervalDrafts.value,
      [pl.id]: Number(pl.interval_minutes),
    }
    intervalErrors.value = {
      ...intervalErrors.value,
      [pl.id]: err?.response?.data?.detail || t('monitor.failedApplyInterval'),
    }
  } finally {
    applyingInterval.value = { ...applyingInterval.value, [pl.id]: false }
  }
}

async function onCheck(pl) {
  checking.value = { ...checking.value, [pl.id]: true }
  actionErrors.value = { ...actionErrors.value, [pl.id]: '' }
  try {
    const res = await monitorAPI.checkMonitoredPlaylist(pl.id)
    const data = res.data || {}
    const { status: _status, downloaded: _downloaded, ...playlist } = data
    if (playlist.id) {
      Object.assign(pl, playlist)
      intervalDrafts.value = {
        ...intervalDrafts.value,
        [pl.id]: Number(pl.interval_minutes),
      }
    } else {
      await load()
    }
  } catch (err) {
    actionErrors.value = {
      ...actionErrors.value,
      [pl.id]: err?.response?.data?.detail || t('monitor.checkFailed'),
    }
  } finally {
    checking.value = { ...checking.value, [pl.id]: false }
  }
}

async function onDelete(pl) {
  if (!confirm(t('monitor.deletePrompt', { name: pl.name }))) return
  try {
    await monitorAPI.deleteMonitoredPlaylist(pl.id)
    playlists.value = playlists.value.filter((p) => p.id !== pl.id)
    const { [pl.id]: _removed, ...rest } = intervalDrafts.value
    intervalDrafts.value = rest
    const { [pl.id]: _removedError, ...restErrors } = intervalErrors.value
    intervalErrors.value = restErrors
    // Keep the shared artist-monitor state in sync so library/player badges
    // stop showing "Monitoring" immediately after removal.
    if (pl.kind === 'artist') removeMonitoredArtist(pl)
  } catch {
    // silently ignore
  }
}

function formatInterval(minutes) {
  if (minutes < 60) return `${minutes} ${t('monitor.minSuffix')}`
  if (minutes < 1440) return `${minutes / 60} ${t('monitor.hourSuffix')}`
  if (minutes < 10080) {
    const days = minutes / 1440
    return `${days} ${
      days === 1 ? t('monitor.daySuffix') : t('monitor.daysSuffix')
    }`
  }
  if (minutes < 43200) {
    const weeks = minutes / 10080
    return `${weeks} ${
      weeks === 1 ? t('monitor.weekSuffix') : t('monitor.weeksSuffix')
    }`
  }
  const months = Math.round(minutes / 43200)
  return `${months} ${
    months === 1 ? t('monitor.monthSuffix') : t('monitor.monthsSuffix')
  }`
}

function timeAgo(isoString) {
  try {
    const diff = Date.now() - new Date(isoString).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return t('monitor.timeJustNow')
    if (mins < 60) return t('monitor.timeMinAgo', { n: mins })
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return t('monitor.timeHourAgo', { n: hrs })
    return t('monitor.timeDayAgo', { n: Math.floor(hrs / 24) })
  } catch {
    return ''
  }
}

onMounted(load)
</script>

<style scoped>
.monitor-view {
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

.monitor-page {
  @apply mx-auto flex w-full max-w-4xl flex-1 flex-col min-w-0 min-h-0 overflow-hidden px-4 py-3 sm:px-6 sm:py-8;
}

.monitor-page > .mobile-page-header,
.monitor-page > .surface:not(.monitor-list-panel),
.monitor-page > .mt-8 {
  @apply shrink-0;
}

.monitor-card {
  @apply min-w-0 overflow-hidden;
  min-height: 12.25rem;
}

.monitor-list-panel {
  @apply flex min-h-0 flex-1 flex-col overflow-hidden;
}

.monitor-list-scroll {
  @apply min-h-0 flex-1 overflow-x-hidden overflow-y-auto pr-1;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.monitor-list-scroll::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.monitor-card-grid {
  @apply grid min-w-0 grid-cols-1 gap-3;
}

.monitor-target-search {
  z-index: 2;
}

.monitor-search-results {
  max-height: min(18rem, 42dvh);
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 719px) {
  .monitor-header {
    @apply mb-3;
  }

  .monitor-add-panel {
    @apply mb-3 p-4;
  }

  .monitor-add-panel h2 {
    @apply mb-3;
  }

  .monitor-add-form {
    @apply space-y-2;
  }

  .monitor-add-form input,
  .monitor-add-form select,
  .monitor-add-form button {
    height: 2.875rem;
  }

  .monitor-target-search {
    z-index: 3;
  }

  .monitor-list-panel {
    @apply mb-3 p-3;
  }

  .monitor-list-panel > div:first-child {
    @apply mb-2;
  }

  .monitor-card-grid {
    @apply gap-2;
  }

  .monitor-card {
    min-height: 10.25rem;
    padding: 0.625rem;
  }

  .monitor-card :deep(.monitor-card-cover) {
    height: 4.25rem;
    width: 4.25rem;
    border-radius: 0.875rem;
  }

  .monitor-card .monitor-action-btn,
  .monitor-card .select {
    height: 2.25rem;
  }

  .monitor-card .btn {
    height: 2.25rem;
    min-height: 2.25rem;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }

  .monitor-info {
    @apply hidden;
  }
}

@media (min-width: 720px) {
  .monitor-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .monitor-page {
    @apply py-5;
  }

  .monitor-header {
    @apply mb-4;
  }

  .monitor-add-panel {
    @apply mb-4 p-4;
  }

  .monitor-add-panel h2 {
    @apply mb-3;
  }

  .monitor-add-form {
    display: grid;
    grid-template-columns: minmax(13rem, 1fr) minmax(18rem, 2fr) minmax(
        18rem,
        1.35fr
      );
    align-items: stretch;
    gap: 0.75rem;
  }

  .monitor-add-form > * {
    min-width: 0;
  }

  .monitor-add-form > :not([hidden]) ~ :not([hidden]) {
    margin-top: 0;
  }

  .monitor-list-panel {
    @apply mb-4;
  }

  .monitor-info {
    @apply hidden;
  }

  .monitor-card {
    min-height: 8.9rem;
  }

  .monitor-card :deep(.monitor-card-cover) {
    height: 4rem;
    width: 4rem;
    border-radius: 0.875rem;
  }

  .monitor-card .monitor-action-btn,
  .monitor-card .select {
    height: 2.25rem;
  }

  .monitor-card .btn {
    height: 2.25rem;
    min-height: 2.25rem;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }
}

.monitor-card-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.monitor-action-btn {
  @apply flex h-11 items-center justify-center rounded-xl border border-white/10 bg-base-100/55 text-base-content/80 transition-colors hover:border-primary/40 hover:bg-primary/10 hover:text-primary disabled:cursor-not-allowed disabled:opacity-50;
}

.monitor-action-btn-danger {
  @apply border-error/20 text-error/75 hover:border-error/55 hover:bg-error/10 hover:text-error focus-visible:border-error/60 focus-visible:bg-error/10 focus-visible:text-error;
}

.monitor-action-btn-pause {
  @apply border-amber-300/25 text-amber-200 hover:border-amber-300/60 hover:bg-amber-300/10 hover:text-amber-100 focus-visible:border-amber-300/70 focus-visible:bg-amber-300/10 focus-visible:text-amber-100;
}

[data-theme='downtify-light'] .monitor-action-btn-pause {
  @apply border-amber-500/30 text-amber-700 hover:border-amber-500/60 hover:bg-amber-400/15 hover:text-amber-800 focus-visible:border-amber-500/70 focus-visible:bg-amber-400/15 focus-visible:text-amber-800;
}
</style>
