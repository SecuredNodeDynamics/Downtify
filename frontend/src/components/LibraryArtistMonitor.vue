<template>
  <div class="library-artist-monitor shrink-0">
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
      class="btn btn-sm inline-flex h-10 items-center gap-1.5 rounded-full px-3 sm:px-4"
      :class="
        artistNotFound
          ? 'border-error bg-error/5 text-error hover:bg-error/10'
          : 'border-white/10 bg-base-100/85 hover:bg-base-100'
      "
      :disabled="busy"
      @click="startMonitor"
    >
      <span v-if="busy" class="loading loading-spinner loading-xs" />
      <Icon
        v-else
        :icon="artistNotFound ? 'clarity:warning-standard-line' : 'clarity:eye-line'"
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
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import monitorAPI from '/src/model/monitor.js'
import {
  findMonitoredArtist,
  monitoredArtists,
  refreshMonitoredArtists,
} from '/src/model/monitoredArtists.js'
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
const artistNotFound = ref(false)
const pickerError = ref('')
const pickerOpen = ref(false)
const pickerMatches = ref([])

const monitoredEntry = computed(() => {
  monitoredArtists.value
  return findMonitoredArtist(props.artistName)
})

async function lookupSpotifyArtistsWithRetry(artistName, limit = 5) {
  const lookup = () =>
    monitorAPI.lookupSpotifyArtists(artistName, limit).then((res) => {
      const matches = Array.isArray(res.data?.matches) ? res.data.matches : []
      return { res, matches }
    })

  let { res, matches } = await lookup()
  if (matches.length === 0) {
    await new Promise((resolve) => setTimeout(resolve, 1500))
    ;({ res, matches } = await lookup())
  }
  return { res, matches }
}

async function startMonitor() {
  if (!props.artistName || busy.value) return
  busy.value = true
  artistNotFound.value = false
  pickerError.value = ''
  try {
    const { matches } = await lookupSpotifyArtistsWithRetry(props.artistName)
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
    artistNotFound.value = true
  } finally {
    busy.value = false
  }
}

async function addMatch(match) {
  if (!match?.url) return
  busy.value = true
  pickerError.value = ''
  try {
    await monitorAPI.addMonitoredPlaylist(match.url, 60, 'artist')
    pickerOpen.value = false
    pickerMatches.value = []
    artistNotFound.value = false
    await refreshMonitoredArtists()
  } catch (err) {
    if (err?.response?.status === 409) {
      pickerOpen.value = false
      await refreshMonitoredArtists()
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
    artistNotFound.value = false
    pickerError.value = ''
  }
)

onMounted(() => {
  void refreshMonitoredArtists()
})
</script>
