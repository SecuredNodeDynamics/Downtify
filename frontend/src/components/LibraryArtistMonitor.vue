<template>
  <div class="library-artist-monitor">
    <button
      v-if="monitoredEntry"
      type="button"
      class="btn btn-sm inline-flex h-10 items-center gap-1.5 rounded-full px-3 sm:px-4"
      :class="
        monitoredEntry.enabled
          ? 'btn-primary'
          : 'border-white/10 bg-base-100/85 hover:bg-base-100'
      "
      @click="goToMonitor"
    >
      <Icon icon="clarity:eye-line" class="h-4 w-4 shrink-0" />
      <span class="text-xs sm:text-sm">
        {{
          monitoredEntry.enabled
            ? t('library.monitoringArtist')
            : t('library.monitorPaused')
        }}
      </span>
    </button>

    <button
      v-else
      type="button"
      class="monitor-action-btn btn btn-sm inline-flex h-10 items-center gap-1.5 rounded-full border-white/10 bg-base-100/85 px-3 hover:bg-base-100 sm:px-4"
      :class="monitorButtonClass"
      :disabled="busy"
      @click="startMonitor"
    >
      <Icon
        :icon="monitorButtonIcon"
        class="h-4 w-4 shrink-0"
      />
      <span class="text-xs sm:text-sm">
        {{ monitorButtonLabel }}
      </span>
    </button>

    <p v-if="actionError" class="monitor-alert" role="alert">
      <Icon icon="clarity:warning-line" class="h-3.5 w-3.5 shrink-0" />
      {{ actionError }}
    </p>

    <div
      v-if="pickerOpen"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center"
      @click.self="closePicker"
    >
      <div
        class="surface-strong w-full max-w-lg overflow-hidden rounded-3xl border border-white/10 shadow-glow-md"
        role="dialog"
        aria-modal="true"
      >
        <div class="border-b border-white/10 px-5 py-4">
          <h3 class="text-lg font-semibold">
            {{ t('library.monitorArtistPickTitle') }}
          </h3>
          <p class="mt-1 text-sm text-base-content/60">
            {{ t('library.monitorArtistPickSubtitle', { artist: artistName }) }}
          </p>
        </div>

        <div class="max-h-[24rem] space-y-2 overflow-y-auto p-4">
          <p
            v-if="pickerMatches.length === 0"
            class="rounded-2xl border border-warning/20 bg-warning/10 px-4 py-3 text-sm text-warning"
          >
            {{ t('library.monitorArtistManualHint') }}
          </p>
          <button
            v-for="match in pickerMatches"
            :key="match.spotify_id"
            type="button"
            class="flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-base-100/70 p-3 text-left transition-colors hover:border-primary/45 hover:bg-base-100/90"
            :disabled="busy"
            @click="addMatch(match)"
          >
            <div
              class="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-primary/10"
            >
              <img
                v-if="match.image_url"
                :src="match.image_url"
                :alt="match.name"
                class="h-full w-full object-cover"
                loading="lazy"
              />
              <Icon
                v-else
                icon="clarity:user-line"
                class="h-6 w-6 text-primary/70"
              />
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate font-semibold">{{ match.name }}</p>
              <p class="text-xs text-base-content/50">
                {{
                  t('library.monitorArtistMatchScore', {
                    score: Math.round((match.match_score || 0) * 100),
                  })
                }}
              </p>
            </div>
            <Icon
              icon="clarity:angle-line"
              class="h-4 w-4 shrink-0 text-base-content/35"
            />
          </button>
        </div>

        <div class="border-t border-white/10 px-5 py-4 space-y-2">
          <form class="space-y-2" @submit.prevent="addManualArtistUrl">
            <label
              class="block text-xs font-semibold uppercase tracking-wide text-base-content/45"
            >
              {{ t('library.monitorArtistSpotifyUrlLabel') }}
            </label>
            <div class="flex flex-col gap-2 sm:flex-row">
              <input
                v-model.trim="manualSpotifyUrl"
                type="url"
                inputmode="url"
                autocomplete="off"
                class="input input-sm min-h-10 flex-1 rounded-full border-white/10 bg-base-100/85"
                :placeholder="t('library.monitorArtistSpotifyUrlPlaceholder')"
                :disabled="busy"
              />
              <button
                type="submit"
                class="btn btn-primary btn-sm h-10 rounded-full px-4"
                :disabled="busy || !manualSpotifyUrl"
              >
                {{ t('library.monitorArtistUseUrl') }}
              </button>
            </div>
          </form>
          <p v-if="pickerError" class="text-center text-sm text-error">
            {{ pickerError }}
          </p>
          <button
            type="button"
            class="btn btn-sm h-10 w-full rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
            :disabled="busy"
            @click="closePicker"
          >
            {{ t('common.cancel') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import monitorAPI from '/src/model/monitor.js'
import { EMBEDDED_SERVER_READY_EVENT } from '../model/embeddedServer.js'
import {
  buildApiBaseUrl,
  getServerConfig,
  usesEmbeddedServer,
} from '../model/serverConnection.js'
import {
  findMonitoredArtist,
  monitoredArtistMap,
  monitoredArtists,
  normalizeMonitoredArtistName,
  refreshMonitoredArtists,
  upsertMonitoredArtist,
} from '../model/monitoredArtists.js'
import { useI18n } from '/src/i18n'

const props = defineProps({
  artistName: {
    type: String,
    required: true,
  },
})

const { t } = useI18n()
const router = useRouter()

const busy = ref(false)
const monitorButtonState = ref('')
const actionError = ref('')
const artistNotFound = ref(false)
const pickerError = ref('')
const pickerOpen = ref(false)
const pickerMatches = ref([])
const manualSpotifyUrl = ref('')
const MIN_MONITOR_STARTING_MS = 900
const RESET_MONITOR_STATE_MS = 2500

const monitorButtonClass = computed(() => ({
  'monitor-not-found-btn': artistNotFound.value,
  'monitor-action-btn-starting': monitorButtonState.value === 'starting',
  'monitor-action-btn-confirmed': monitorButtonState.value === 'confirmed',
  'monitor-action-btn-failed': monitorButtonState.value === 'failed',
}))

const monitorButtonIcon = computed(() => {
  if (monitorButtonState.value === 'starting') return 'clarity:sync-line'
  if (monitorButtonState.value === 'confirmed') {
    return 'clarity:check-circle-line'
  }
  if (monitorButtonState.value === 'failed' || artistNotFound.value) {
    return 'clarity:warning-line'
  }
  return 'clarity:eye-line'
})

const monitorButtonLabel = computed(() => {
  if (monitorButtonState.value === 'starting') {
    return t('library.monitorArtistStarting')
  }
  if (monitorButtonState.value === 'confirmed') {
    return t('library.monitoringArtist')
  }
  if (monitorButtonState.value === 'failed') return t('library.monitorFailed')
  return artistNotFound.value
    ? t('library.monitorArtistNotFoundShort')
    : t('library.monitorArtist')
})

function setMonitorButtonStateAfterPress(state, pressedAt) {
  const elapsed = Date.now() - pressedAt
  window.setTimeout(
    () => {
      monitorButtonState.value = state
    },
    Math.max(0, MIN_MONITOR_STARTING_MS - elapsed)
  )
}

function resetMonitorButtonState(state, delay = RESET_MONITOR_STATE_MS) {
  window.setTimeout(() => {
    if (monitorButtonState.value === state) monitorButtonState.value = ''
  }, delay)
}

function confirmMonitorButton(pressedAt) {
  setMonitorButtonStateAfterPress('confirmed', pressedAt)
}

function failMonitorButton(pressedAt) {
  setMonitorButtonStateAfterPress('failed', pressedAt)
  resetMonitorButtonState('failed')
}

async function ensureBackendReady() {
  if (!usesEmbeddedServer()) return true
  const baseUrl = buildApiBaseUrl(getServerConfig())
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const res = await fetch(`${baseUrl}/api/version`, { cache: 'no-store' })
      if (res.ok) return true
    } catch {
      // Embedded server still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 500))
  }
  return false
}

const monitoredEntry = computed(() => {
  monitoredArtistMap.value
  return findMonitoredArtist(props.artistName)
})

function dedupeArtistMatches(matches = []) {
  const seenIds = new Set()
  const seenNames = new Set()
  const deduped = []

  for (const match of matches) {
    const spotifyId = String(match?.spotify_id || '').trim()
    const nameKey = normalizeMonitoredArtistName(match?.name)
    if (spotifyId && seenIds.has(spotifyId)) continue
    if (nameKey && seenNames.has(nameKey)) continue
    if (spotifyId) seenIds.add(spotifyId)
    if (nameKey) seenNames.add(nameKey)
    deduped.push(match)
  }

  return deduped.sort(
    (left, right) => (right?.match_score || 0) - (left?.match_score || 0)
  )
}

function findMonitoredArtistBySpotifyId(spotifyId) {
  const id = String(spotifyId || '').trim()
  if (!id) return null
  return (
    monitoredArtists.value.find(
      (item) =>
        item.kind === 'artist' && String(item.spotify_id || '').trim() === id
    ) || null
  )
}

function linkExistingMonitoredArtist(match) {
  const linked =
    findMonitoredArtist(props.artistName) ||
    findMonitoredArtist(match?.name) ||
    findMonitoredArtistBySpotifyId(match?.spotify_id)
  if (linked) {
    upsertMonitoredArtist(linked, props.artistName)
    return true
  }
  return false
}

async function lookupSpotifyArtistsWithRetry(artistName, limit = 5) {
  const lookup = () =>
    monitorAPI.lookupSpotifyArtists(artistName, limit).then((res) => {
      const matches = Array.isArray(res.data?.matches) ? res.data.matches : []
      return { res, matches }
    })

  let { res, matches } = await lookup()
  if (matches.length === 0) {
    await new Promise((resolve) => setTimeout(resolve, 250))
    ;({ res, matches } = await lookup())
  }
  return { res, matches }
}

async function startMonitor() {
  if (!props.artistName || busy.value) return
  if (artistNotFound.value) {
    openManualArtistPicker()
    return
  }
  const pressedAt = Date.now()
  busy.value = true
  monitorButtonState.value = 'starting'
  actionError.value = ''
  artistNotFound.value = false
  pickerError.value = ''
  try {
    if (!(await ensureBackendReady())) {
      actionError.value = t('library.monitorArtistLookupFailed')
      failMonitorButton(pressedAt)
      return
    }

    const { matches: rawMatches } = await lookupSpotifyArtistsWithRetry(
      props.artistName
    )
    const matches = dedupeArtistMatches(rawMatches)
    if (matches.length === 0) {
      artistNotFound.value = true
      failMonitorButton(pressedAt)
      openManualArtistPicker()
      return
    }

    const strongMatches = matches.filter((match) => match.match_score >= 0.72)
    if (strongMatches.length === 1) {
      await addMatch(strongMatches[0], pressedAt)
      return
    }
    if (matches.length === 1) {
      await addMatch(matches[0], pressedAt)
      return
    }

    monitorButtonState.value = ''
    pickerMatches.value = matches
    manualSpotifyUrl.value = ''
    pickerOpen.value = true
  } catch {
    artistNotFound.value = true
    failMonitorButton(pressedAt)
    pickerError.value = t('library.monitorArtistLookupFailed')
    openManualArtistPicker()
  } finally {
    busy.value = false
  }
}

function openManualArtistPicker() {
  pickerMatches.value = []
  manualSpotifyUrl.value = ''
  pickerOpen.value = true
}

function monitorUrlForMatch(match) {
  const url = String(match?.url || '').trim()
  if (url) return url
  const spotifyId = String(match?.spotify_id || '').trim()
  if (!spotifyId) return ''
  return `https://open.spotify.com/artist/${spotifyId}`
}

function spotifyArtistIdFromUrl(url) {
  const value = String(url || '').trim()
  const match = value.match(
    /^(?:https?:\/\/open\.spotify\.com\/artist\/|spotify:artist:)([A-Za-z0-9]+)(?:[/?#].*)?$/i
  )
  return match?.[1] || ''
}

async function addMatch(match, pressedAt = Date.now()) {
  const url = monitorUrlForMatch(match)
  if (!url) {
    pickerError.value = t('library.monitorArtistAddFailed')
    failMonitorButton(pressedAt)
    return
  }

  monitorButtonState.value = 'starting'
  if (linkExistingMonitoredArtist(match)) {
    pickerOpen.value = false
    pickerMatches.value = []
    actionError.value = ''
    artistNotFound.value = false
    confirmMonitorButton(pressedAt)
    return
  }

  busy.value = true
  pickerError.value = ''
  try {
    const res = await monitorAPI.addMonitoredPlaylist(url, 60, 'artist')
    pickerOpen.value = false
    pickerMatches.value = []
    actionError.value = ''
    artistNotFound.value = false
    upsertMonitoredArtist(res.data, props.artistName)
    confirmMonitorButton(pressedAt)
    void refreshMonitoredArtists()
  } catch (err) {
    if (err?.response?.status === 409) {
      pickerOpen.value = false
      await refreshMonitoredArtists({ force: true })
      linkExistingMonitoredArtist(match)
      confirmMonitorButton(pressedAt)
      return
    }
    pickerError.value =
      err?.response?.data?.detail || t('library.monitorArtistAddFailed')
    failMonitorButton(pressedAt)
  } finally {
    busy.value = false
  }
}

async function addManualArtistUrl() {
  const spotifyId = spotifyArtistIdFromUrl(manualSpotifyUrl.value)
  if (!spotifyId) {
    pickerError.value = t('library.monitorArtistInvalidSpotifyUrl')
    return
  }
  await addMatch({
    spotify_id: spotifyId,
    name: props.artistName,
    url: `https://open.spotify.com/artist/${spotifyId}`,
    match_score: 1,
  }, Date.now())
}

function closePicker() {
  if (busy.value) return
  pickerOpen.value = false
  pickerMatches.value = []
  manualSpotifyUrl.value = ''
}

function goToMonitor() {
  router.push({ name: 'Monitor' })
}

watch(
  () => props.artistName,
  () => {
    pickerError.value = ''
    actionError.value = ''
    monitorButtonState.value = ''
  }
)

function handleEmbeddedServerReady() {
  if (!usesEmbeddedServer()) return
  if (actionError.value) actionError.value = ''
}

watch(
  () => props.artistName,
  () => {
    actionError.value = ''
    artistNotFound.value = false
    monitorButtonState.value = ''
  }
)

onMounted(() => {
  void refreshMonitoredArtists()
  if (usesEmbeddedServer()) {
    window.addEventListener(
      EMBEDDED_SERVER_READY_EVENT,
      handleEmbeddedServerReady
    )
  }
})

onUnmounted(() => {
  if (usesEmbeddedServer()) {
    window.removeEventListener(
      EMBEDDED_SERVER_READY_EVENT,
      handleEmbeddedServerReady
    )
  }
})
</script>

<style scoped>
.library-artist-monitor {
  @apply flex min-w-0 max-w-full shrink-0 flex-col items-end gap-1;
}

.monitor-alert {
  @apply flex max-w-full items-start gap-1.5 rounded-lg border border-error/25 bg-error/10 px-2.5 py-1.5 text-left text-xs leading-snug text-error;
}

.monitor-not-found-btn {
  @apply border-error/50 bg-error/10 text-error hover:border-error/70 hover:bg-error/15;
}

.monitor-action-btn {
  @apply relative overflow-hidden transition-all duration-200 active:scale-95;
}

.monitor-action-btn-starting {
  @apply scale-[1.03] ring-2 ring-primary/60 ring-offset-2 ring-offset-base-100;
  animation: monitor-button-pulse 0.8s ease-in-out infinite;
}

.monitor-action-btn-starting::after {
  content: '';
  position: absolute;
  inset: -40% -60%;
  background: linear-gradient(
    100deg,
    transparent 35%,
    rgba(255, 255, 255, 0.42) 50%,
    transparent 65%
  );
  animation: monitor-button-sheen 0.95s linear infinite;
}

.monitor-action-btn-starting :deep(svg) {
  animation: monitor-button-spin 0.9s linear infinite;
}

.monitor-action-btn-confirmed {
  @apply bg-emerald-400 text-black shadow-glow-sm ring-2 ring-emerald-200/70;
  animation: monitor-button-pop 0.36s ease-out both;
}

.monitor-action-btn-failed {
  @apply bg-error text-error-content ring-2 ring-error/60;
  animation: monitor-button-pop 0.28s ease-out both;
}

@keyframes monitor-button-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.48);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(34, 197, 94, 0);
  }
}

@keyframes monitor-button-sheen {
  from {
    transform: translateX(-55%);
  }
  to {
    transform: translateX(55%);
  }
}

@keyframes monitor-button-pop {
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

@keyframes monitor-button-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
