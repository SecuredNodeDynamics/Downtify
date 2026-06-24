<template>
  <div class="min-h-0 overflow-x-hidden">
    <Navbar />

    <div class="mx-auto max-w-4xl w-full min-w-0 px-4 py-4 sm:py-8 sm:px-6">
      <!-- Header -->
      <div class="mb-6 sm:mb-8 mobile-page-header">
        <h1 class="text-2xl font-bold tracking-tight">
          {{ t('monitor.title') }}
        </h1>
        <p class="mt-1 text-sm text-base-content/60">
          {{ t('monitor.subtitle') }}
        </p>
      </div>

      <!-- Add form -->
      <div
        class="surface rounded-2xl p-4 sm:p-5 mb-6 sm:mb-8 min-w-0 overflow-hidden"
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
          <input
            v-model="newUrl"
            type="url"
            inputmode="url"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
            :placeholder="urlPlaceholder"
            class="input-modern input-modern-plain w-full min-w-0 h-12 text-base sm:text-sm"
            :disabled="adding"
          />
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
              :disabled="adding || !newUrl.trim()"
            >
              <span v-if="adding" class="loading loading-spinner loading-xs" />
              <span v-else>{{ t('monitor.watch') }}</span>
            </button>
          </div>
        </form>
        <p v-if="addError" class="mt-2 text-xs text-error">{{ addError }}</p>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="skeleton h-24 rounded-2xl" />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="playlists.length === 0"
        class="surface rounded-2xl p-12 flex flex-col items-center text-center"
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

      <!-- Item cards -->
      <ul v-else class="space-y-3">
        <li
          v-for="pl in playlists"
          :key="pl.id"
          class="surface rounded-2xl p-4 sm:p-5"
        >
          <div class="flex gap-4 min-w-0">
            <div class="shrink-0">
              <CoverImage
                :src="coverForItem(pl).src"
                :fallbacks="coverForItem(pl).fallbacks"
                :alt="pl.name"
                img-class="h-16 w-16 sm:h-20 sm:w-20 rounded-2xl object-cover border border-white/10 bg-base-100/60"
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
            </div>

            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 mb-1 flex-wrap">
                <span class="font-semibold truncate">{{ pl.name }}</span>
                <span class="pill shrink-0 badge-neutral-soft text-xs">
                  {{
                    pl.kind === 'artist'
                      ? t('monitor.kindArtist')
                      : t('monitor.kindPlaylist')
                  }}
                </span>
                <span
                  class="pill shrink-0"
                  :class="pl.enabled ? 'badge-soft' : 'badge-neutral-soft'"
                >
                  {{ pl.enabled ? t('monitor.active') : t('monitor.paused') }}
                </span>
              </div>
              <div
                class="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-base-content/50"
              >
                <span>
                  <Icon
                    icon="clarity:refresh-line"
                    class="inline h-3 w-3 mr-0.5"
                  />
                  {{
                    t('monitor.everyInterval', {
                      interval: formatInterval(pl.interval_minutes),
                    })
                  }}
                </span>
                <span>
                  <Icon
                    icon="clarity:music-note-line"
                    class="inline h-3 w-3 mr-0.5"
                  />
                  {{
                    pl.last_track_count === 1
                      ? t('monitor.tracksOne', { count: pl.last_track_count })
                      : t('monitor.tracksMany', { count: pl.last_track_count })
                  }}
                </span>
                <span v-if="pl.last_checked">
                  <Icon
                    icon="clarity:clock-line"
                    class="inline h-3 w-3 mr-0.5"
                  />
                  {{ t('monitor.checked', { when: timeAgo(pl.last_checked) }) }}
                </span>
                <span v-else class="italic">{{ t('monitor.notChecked') }}</span>
              </div>
            </div>
          </div>

          <div
            class="mt-4 flex flex-wrap items-center justify-end gap-2 border-t border-white/5 pt-4"
          >
            <select
              :value="draftInterval(pl)"
              class="select select-sm rounded-full border border-white/10 bg-base-100/60 text-xs focus:border-primary/60 min-w-[6.5rem]"
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
              class="btn btn-sm h-9 rounded-full px-4"
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

            <button
              class="icon-btn"
              :title="pl.enabled ? t('monitor.pause') : t('monitor.resume')"
              @click="onToggle(pl)"
            >
              <Icon
                :icon="pl.enabled ? 'clarity:pause-line' : 'clarity:play-line'"
                class="h-4 w-4"
              />
            </button>

            <button
              class="icon-btn"
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
              class="icon-btn text-error/70 hover:text-error hover:bg-error/10"
              :title="t('monitor.stop')"
              @click="onDelete(pl)"
            >
              <Icon icon="clarity:trash-line" class="h-4 w-4" />
            </button>
          </div>
          <p
            v-if="intervalErrors[pl.id] || actionErrors[pl.id]"
            class="mt-2 text-right text-[11px] leading-snug text-error"
          >
            {{ intervalErrors[pl.id] || actionErrors[pl.id] }}
          </p>
        </li>
      </ul>

      <!-- Info banner -->
      <div
        class="mt-8 surface rounded-2xl p-4 flex gap-3 text-sm text-base-content/60"
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
import { ref, computed, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import Navbar from '/src/components/Navbar.vue'
import CoverImage from '/src/components/CoverImage.vue'
import monitorAPI from '/src/model/monitor.js'
import API from '/src/model/api.js'
import { useI18n } from '/src/i18n'

const { t } = useI18n()

const playlists = ref([])
const loading = ref(false)
const adding = ref(false)
const addError = ref('')
const newUrl = ref('')
const newKind = ref('playlist')
const newInterval = ref(60)
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

async function load() {
  loading.value = true
  try {
    const res = await monitorAPI.listMonitoredPlaylists()
    setPlaylists(res.data || [])
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
  if (pl?.kind === 'artist') {
    const local = API.coverSourcesForArtist(pl.name)
    const fallbacks = []
    if (spotifyUrl && local.src) fallbacks.push(local.src)
    fallbacks.push(...local.fallbacks)
    return {
      src: spotifyUrl || local.src,
      fallbacks: [...new Set(fallbacks.filter(Boolean))],
    }
  }
  return {
    src: spotifyUrl,
    fallbacks: [],
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
      newUrl.value.trim(),
      newInterval.value,
      newKind.value
    )
    setPlaylists([res.data, ...playlists.value])
    newUrl.value = ''
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
      [pl.id]:
        err?.response?.data?.detail || t('monitor.failedUpdate'),
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
      [pl.id]:
        err?.response?.data?.detail || t('monitor.failedApplyInterval'),
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
      [pl.id]:
        err?.response?.data?.detail || t('monitor.checkFailed'),
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
