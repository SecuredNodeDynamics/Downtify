<template>
  <div class="player-view min-h-0 overflow-x-hidden">
    <Navbar />

    <div
      class="player-page mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 py-2 sm:px-6 sm:py-8 min-h-0"
    >
      <!-- Header -->
      <div class="mb-4 sm:mb-8 mobile-page-header shrink-0">
        <h1 class="text-2xl font-bold tracking-tight">
          {{ t('player.title') }}
        </h1>
        <p class="mt-1 text-sm text-base-content/60">
          {{ t('player.subtitle') }}
        </p>
      </div>

      <!-- Empty state -->
      <div
        v-if="files.length === 0 && !loading"
        class="surface rounded-2xl p-12 flex flex-col items-center text-center"
      >
        <Icon
          icon="clarity:headphones-line"
          class="h-12 w-12 text-base-content/20 mb-4"
        />
        <p class="text-base-content/50 text-sm">{{ t('player.empty') }}</p>
        <p class="text-base-content/40 text-xs mt-1">
          {{ t('player.emptyHint') }}
        </p>
      </div>

      <!-- Skeleton -->
      <div v-else-if="loading && !player.currentTrack.value" class="space-y-3">
        <div class="skeleton h-52 rounded-3xl lg:h-72" />
        <div class="skeleton h-16 rounded-2xl" />
        <div class="skeleton h-16 rounded-2xl" />
      </div>

      <!-- Player + queue -->
      <div v-else class="player-shell min-h-0 flex-1">
        <!-- Now playing -->
        <section class="player-now surface rounded-3xl p-4 sm:p-8 flex flex-col items-center text-center">
          <p
            class="mb-3 w-full text-left text-xs font-semibold uppercase tracking-wider text-base-content/50 lg:hidden"
          >
            {{ t('player.nowPlaying') }}
          </p>

          <!-- Cover -->
          <div
            class="player-cover relative flex items-center justify-center overflow-hidden rounded-2xl bg-primary/10 text-primary shadow-glow sm:rounded-3xl"
            :class="{ 'pulse-glow': player.isPlaying.value }"
          >
            <img
              v-if="
                player.currentTrack.value &&
                player.currentTrack.value.cover &&
                !coverFailed[player.currentTrack.value.file]
              "
              :src="player.currentTrack.value.cover"
              :alt="player.currentTrack.value.title"
              class="absolute inset-0 h-full w-full object-cover"
              @error="markCoverFailed(player.currentTrack.value.file)"
            />
            <Icon v-else icon="clarity:music-note-line" class="h-16 w-16 sm:h-24 sm:w-24" />
            <div
              v-if="player.isPlaying.value"
              class="absolute bottom-2 right-2 equalizer h-5 sm:bottom-3 sm:right-3"
              aria-hidden="true"
            >
              <span></span><span></span><span></span>
            </div>
          </div>

          <!-- Title / artist -->
          <div class="mt-4 w-full sm:mt-6">
            <p class="text-lg font-bold tracking-tight truncate sm:text-xl">
              {{ trackTitle }}
            </p>
            <p class="mt-0.5 text-sm text-base-content/60 truncate">
              {{ trackArtist }}
            </p>
          </div>

          <!-- Progress -->
          <div class="mt-4 w-full sm:mt-6">
            <div
              class="player-progress"
              ref="progressBar"
              @click="onSeekClick"
              @pointerdown="onSeekStart"
            >
              <div class="player-progress-track">
                <div
                  class="player-progress-fill"
                  :style="`width: ${player.progressPct.value}%`"
                />
                <div
                  class="player-progress-thumb"
                  :style="`left: calc(${player.progressPct.value}% - 7px)`"
                />
              </div>
            </div>
            <div
              class="mt-1 flex items-center justify-between text-xs text-base-content/50 tabular-nums sm:mt-2"
            >
              <span>{{ formatTime(player.currentTime.value) }}</span>
              <span>{{ formatTime(player.duration.value) }}</span>
            </div>
          </div>

          <!-- Transport -->
          <div class="mt-4 flex items-center justify-center gap-2 sm:mt-5 sm:gap-3">
            <button
              class="icon-btn h-9 w-9 sm:h-10 sm:w-10"
              :class="{ 'icon-btn-active': player.shuffle.value }"
              @click="player.toggleShuffle()"
              :title="
                player.shuffle.value
                  ? t('player.shuffleOn')
                  : t('player.shuffleOff')
              "
            >
              <Icon icon="clarity:shuffle-line" class="h-4 w-4 sm:h-5 sm:w-5" />
            </button>
            <button
              class="icon-btn h-10 w-10 sm:h-10 sm:w-10"
              @click="player.prev()"
              :title="t('player.previous')"
              :disabled="files.length === 0"
            >
              <Icon
                icon="clarity:step-forward-2-line"
                class="h-5 w-5 -scale-x-100"
              />
            </button>
            <button
              class="player-play-btn inline-flex items-center justify-center rounded-full bg-primary text-primary-content shadow-glow-sm transition hover:scale-105 active:scale-95 disabled:opacity-50"
              @click="player.toggle()"
              :disabled="files.length === 0"
              :title="
                player.isPlaying.value ? t('player.pause') : t('player.play')
              "
            >
              <Icon
                :icon="
                  player.isPlaying.value
                    ? 'clarity:pause-solid'
                    : 'clarity:play-solid'
                "
                class="h-7 w-7 sm:h-6 sm:w-6"
              />
            </button>
            <button
              class="icon-btn h-10 w-10 sm:h-10 sm:w-10"
              @click="player.next()"
              :title="t('player.next')"
              :disabled="files.length === 0"
            >
              <Icon icon="clarity:step-forward-2-line" class="h-5 w-5" />
            </button>
            <button
              class="icon-btn relative h-9 w-9 sm:h-10 sm:w-10"
              :class="{ 'icon-btn-active': player.repeatMode.value !== 'off' }"
              @click="player.cycleRepeat()"
              :title="repeatTitle"
            >
              <Icon icon="clarity:refresh-line" class="h-4 w-4 sm:h-5 sm:w-5" />
              <span
                v-if="player.repeatMode.value === 'one'"
                class="absolute -bottom-0.5 -right-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-primary px-1 text-[9px] font-bold text-primary-content"
              >
                1
              </span>
            </button>
          </div>

          <!-- Volume (desktop only — mobile uses device volume) -->
          <div class="mt-6 hidden w-full max-w-xs items-center gap-3 lg:flex">
            <button
              class="icon-btn"
              @click="player.toggleMute()"
              :title="
                player.isMuted.value ? t('player.unmute') : t('player.mute')
              "
            >
              <Icon
                :icon="
                  player.isMuted.value || player.volume.value === 0
                    ? 'clarity:volume-mute-line'
                    : player.volume.value < 0.5
                      ? 'clarity:volume-down-line'
                      : 'clarity:volume-up-line'
                "
                class="h-5 w-5"
              />
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              :value="player.isMuted.value ? 0 : player.volume.value"
              @input="onVolume($event)"
              class="player-range flex-1"
              :title="t('player.volume')"
            />
          </div>
        </section>

        <!-- Queue list -->
        <aside class="player-queue surface rounded-3xl p-3 sm:p-5 lg:max-h-[640px] lg:overflow-y-auto">
          <div class="mb-2 flex items-center justify-between gap-2 px-1 sm:mb-3">
            <h2
              class="text-xs font-semibold uppercase tracking-wider text-base-content/50"
            >
              <span class="lg:hidden">{{ t('player.upNext') }}</span>
              <span class="hidden lg:inline">{{ t('player.queue') }}</span>
            </h2>
            <span class="text-[11px] text-base-content/40 shrink-0">
              {{
                visibleFiles.length === 1
                  ? t('player.countOne', { count: visibleFiles.length })
                  : t('player.countMany', { count: visibleFiles.length })
              }}
            </span>
          </div>

          <div
            v-if="libraryFilter"
            class="mb-2 flex items-center gap-2 rounded-xl bg-primary/10 px-3 py-2 text-xs"
          >
            <Icon icon="clarity:search-line" class="h-4 w-4 shrink-0 text-primary" />
            <span class="min-w-0 flex-1 truncate text-base-content/80">
              {{ libraryFilter }}
            </span>
            <button
              type="button"
              class="shrink-0 font-medium text-primary"
              @click="clearLibraryFilter"
            >
              {{ t('player.clearFilter') }}
            </button>
          </div>

          <ul v-if="visibleFiles.length > 0" class="space-y-1">
            <li
              v-for="file in visibleFiles"
              :key="file"
              class="rounded-xl px-2 py-2 flex items-center gap-3 cursor-pointer transition-colors"
              :class="
                isCurrentFile(file)
                  ? 'bg-primary/10 text-primary'
                  : 'hover:bg-white/5'
              "
              @click="onPickByFile(file)"
            >
              <div
                class="relative h-9 w-9 shrink-0 rounded-lg overflow-hidden flex items-center justify-center"
                :class="
                  isCurrentFile(file)
                    ? 'bg-primary/15'
                    : 'bg-base-100/60'
                "
              >
                <img
                  v-if="!coverFailed[file]"
                  :src="coverUrlFor(file)"
                  :alt="trackInfo(file).title"
                  class="absolute inset-0 h-full w-full object-cover"
                  loading="lazy"
                  @error="markCoverFailed(file)"
                />
                <span
                  v-if="isCurrentFile(file) && player.isPlaying.value"
                  class="relative equalizer h-3"
                  aria-hidden="true"
                >
                  <span></span><span></span><span></span>
                </span>
                <Icon
                  v-else-if="coverFailed[file]"
                  icon="clarity:music-note-line"
                  class="h-4 w-4 text-base-content/50"
                />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm truncate font-medium">
                  {{ trackInfo(file).title }}
                </p>
                <p class="text-[11px] truncate text-base-content/50">
                  {{ trackInfo(file).artist || t('common.unknownArtist') }}
                </p>
              </div>
            </li>
          </ul>

          <div v-else-if="libraryFilter" class="text-center py-10">
            <p class="text-base-content/50 text-sm">
              {{ t('player.noFilterResults') }}
            </p>
          </div>

          <div v-else class="text-center py-10">
            <p class="text-base-content/50 text-sm">{{ t('player.empty') }}</p>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Icon } from '@iconify/vue'
import Navbar from '/src/components/Navbar.vue'
import API from '/src/model/api'
import { usePlayer, formatTime, trackInfoFromFile } from '/src/model/player'
import { useMobileSearch } from '/src/model/mobileSearch'
import { useI18n } from '/src/i18n'

const { t } = useI18n()
const player = usePlayer()
const mobileSearch = useMobileSearch()
const libraryFilter = mobileSearch.libraryFilter

const files = ref([])
const loading = ref(false)
const progressBar = ref(null)
const coverFailed = ref({})
let dragging = false

function coverUrlFor(file) {
  return API.coverFileURL(file)
}

function markCoverFailed(file) {
  coverFailed.value = { ...coverFailed.value, [file]: true }
}

async function load() {
  loading.value = true
  try {
    const res = await API.listDownloads()
    files.value = res.data || []
    // If the player was empty (direct nav to /player), seed the queue
    // with the library so the user has something to play.
    if (player.playlist.value.length === 0 && files.value.length > 0) {
      player.setPlaylist(files.value)
    }
  } finally {
    loading.value = false
  }
}

function onPick(idx) {
  if (
    player.playlist.value.length !== files.value.length ||
    player.playlist.value[idx]?.file !== files.value[idx]
  ) {
    player.setPlaylist(files.value, { startIndex: idx })
  } else {
    player.playAt(idx)
  }
}

function trackInfo(file) {
  return trackInfoFromFile(file)
}

function fileMatchesFilter(file, query) {
  const q = String(query || '')
    .trim()
    .toLowerCase()
  if (!q) return true
  const info = trackInfo(file)
  return [info.title, info.artist, file].some((part) =>
    String(part || '')
      .toLowerCase()
      .includes(q)
  )
}

const visibleFiles = computed(() => {
  const q = libraryFilter.value
  if (!q) return files.value
  return files.value.filter((file) => fileMatchesFilter(file, q))
})

function isCurrentFile(file) {
  return player.currentTrack.value?.file === file
}

function clearLibraryFilter() {
  mobileSearch.clearLibraryFilter()
}

function onPickByFile(file) {
  const idx = files.value.indexOf(file)
  if (idx < 0) return
  onPick(idx)
}

const trackTitle = computed(() => {
  const c = player.currentTrack.value
  if (c && c.title) return c.title
  return t('player.empty')
})

const trackArtist = computed(() => {
  const c = player.currentTrack.value
  if (c && c.artist) return c.artist
  if (c) return t('common.unknownArtist')
  return ''
})

const repeatTitle = computed(() => {
  if (player.repeatMode.value === 'one') return t('player.repeatOne')
  if (player.repeatMode.value === 'all') return t('player.repeatAll')
  return t('player.repeatOff')
})

function onVolume(e) {
  player.setVolume(parseFloat(e.target.value))
}

function ratioFromEvent(e) {
  const el = progressBar.value
  if (!el) return 0
  const rect = el.getBoundingClientRect()
  const x = (e.clientX || 0) - rect.left
  return Math.max(0, Math.min(1, x / rect.width))
}

function onSeekClick(e) {
  player.seekRatio(ratioFromEvent(e))
}

function onSeekStart(e) {
  dragging = true
  player.seekRatio(ratioFromEvent(e))
  window.addEventListener('pointermove', onSeekDrag)
  window.addEventListener('pointerup', onSeekEnd, { once: true })
}

function onSeekDrag(e) {
  if (!dragging) return
  player.seekRatio(ratioFromEvent(e))
}

function onSeekEnd() {
  dragging = false
  window.removeEventListener('pointermove', onSeekDrag)
}

onMounted(() => {
  window.scroll(0, 0)
  load()
})

onUnmounted(() => {
  window.removeEventListener('pointermove', onSeekDrag)
})
</script>

<style scoped>
@media (max-width: 1023px) {
  .player-view {
    display: flex;
    flex-direction: column;
    height: calc(
      100dvh - var(--app-header-height) - var(--app-safe-top) -
        var(--app-bottom-nav-height) - var(--app-safe-bottom)
    );
    overflow: hidden;
  }

  .player-page {
    min-height: 0;
  }

  .player-shell {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    min-height: 0;
  }

  .player-now {
    flex-shrink: 0;
  }

  .player-cover {
    width: min(42vw, 11rem);
    aspect-ratio: 1;
  }

  .player-play-btn {
    height: 3.75rem;
    width: 3.75rem;
  }

  .player-queue {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }
}

@media (min-width: 1024px) {
  .player-shell {
    display: grid;
    grid-template-columns: 1fr 360px;
    gap: 1.5rem;
  }

  .player-cover {
    height: 16rem;
    width: 16rem;
  }

  .player-play-btn {
    height: 3.5rem;
    width: 3.5rem;
  }
}

.player-progress {
  position: relative;
  width: 100%;
  padding: 0.625rem 0;
  cursor: pointer;
  touch-action: none;
}

.player-progress-track {
  position: relative;
  height: 4px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
}

[data-theme='downtify-light'] .player-progress-track {
  background: rgba(0, 0, 0, 0.1);
}

.player-progress-fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: 9999px;
  background: #1ad05c;
  transition: width 150ms ease;
}

.player-progress-thumb {
  position: absolute;
  top: 50%;
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
  transform: translateY(-50%);
  transition: left 150ms ease;
}

.player-range {
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.1);
  height: 4px;
  border-radius: 9999px;
  outline: none;
}
[data-theme='downtify-light'] .player-range {
  background: rgba(0, 0, 0, 0.1);
}
.player-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  cursor: pointer;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
}
.player-range::-moz-range-thumb {
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  border: none;
  cursor: pointer;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
}
.pulse-glow {
  animation: glow 2.4s ease-in-out infinite;
}
@keyframes glow {
  0%,
  100% {
    box-shadow: 0 0 36px rgba(26, 208, 92, 0.3);
  }
  50% {
    box-shadow: 0 0 60px rgba(26, 208, 92, 0.55);
  }
}
</style>
