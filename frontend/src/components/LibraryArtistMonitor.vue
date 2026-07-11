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
      class="btn btn-sm inline-flex h-10 items-center gap-1.5 rounded-full border-white/10 bg-base-100/85 px-3 hover:bg-base-100 sm:px-4"
      :class="{
        'monitor-not-found-btn': artistNotFound,
      }"
      :disabled="busy"
      @click="startMonitor"
    >
      <span v-if="busy" class="loading loading-spinner loading-xs" />
      <Icon
        v-else
        :icon="artistNotFound ? 'clarity:warning-line' : 'clarity:eye-line'"
        class="h-4 w-4 shrink-0"
      />
      <span class="text-xs sm:text-sm">
        {{
          artistNotFound
            ? t('library.monitorArtistNotFoundShort')
            : t('library.monitorArtist')
        }}
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
const actionError = ref('')
const artistNotFound = ref(false)
const pickerError = ref('')
const pickerOpen = ref(false)
const pickerMatches = ref([])

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
  busy.value = true
  actionError.value = ''
  artistNotFound.value = false
  pickerError.value = ''
  try {
    if (!(await ensureBackendReady())) {
      actionError.value = t('library.monitorArtistLookupFailed')
      return
    }

    const { matches: rawMatches } = await lookupSpotifyArtistsWithRetry(
      props.artistName
    )
    const matches = dedupeArtistMatches(rawMatches)
    if (matches.length === 0) {
      artistNotFound.value = true
      return
    }

    const strongMatches = matches.filter((match) => match.match_score >= 0.72)
    if (strongMatches.length === 1) {
      await addMatch(strongMatches[0])
      return
    }
    if (matches.length === 1) {
      await addMatch(matches[0])
      return
    }

    pickerMatches.value = matches
    pickerOpen.value = true
  } catch {
    actionError.value = t('library.monitorArtistLookupFailed')
  } finally {
    busy.value = false
  }
}

function monitorUrlForMatch(match) {
  const url = String(match?.url || '').trim()
  if (url) return url
  const spotifyId = String(match?.spotify_id || '').trim()
  if (!spotifyId) return ''
  return `https://open.spotify.com/artist/${spotifyId}`
}

async function addMatch(match) {
  const url = monitorUrlForMatch(match)
  if (!url) {
    pickerError.value = t('library.monitorArtistAddFailed')
    return
  }

  if (linkExistingMonitoredArtist(match)) {
    pickerOpen.value = false
    pickerMatches.value = []
    actionError.value = ''
    artistNotFound.value = false
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
    void refreshMonitoredArtists()
  } catch (err) {
    if (err?.response?.status === 409) {
      pickerOpen.value = false
      await refreshMonitoredArtists({ force: true })
      linkExistingMonitoredArtist(match)
      return
    }
    pickerError.value =
      err?.response?.data?.detail || t('library.monitorArtistAddFailed')
  } finally {
    busy.value = false
  }
}

function closePicker() {
  if (busy.value) return
  pickerOpen.value = false
  pickerMatches.value = []
}

function goToMonitor() {
  router.push({ name: 'Monitor' })
}

watch(
  () => props.artistName,
  () => {
    pickerError.value = ''
    actionError.value = ''
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
</style>
