<template>
  <div
    v-if="visible"
    class="mini-player"
  >
    <button
      type="button"
      class="mini-player-main"
      :title="t('player.nowPlaying')"
      @click="openPlayer"
      @pointerdown="onPointerDown"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    >
      <div class="mini-player-cover">
        <CoverImage
          v-if="cover.src || cover.fallbacks.length"
          :src="cover.src"
          :fallbacks="cover.fallbacks"
          :alt="title"
          img-class="h-full w-full object-cover"
        />
        <Icon v-else icon="clarity:music-note-line" class="h-5 w-5" />
      </div>
      <div class="min-w-0 flex-1 text-left">
        <p class="truncate text-sm font-semibold">{{ title }}</p>
        <p class="truncate text-xs text-base-content/55">{{ artist }}</p>
      </div>
    </button>

    <div class="mini-player-actions">
      <div ref="volumeRoot" class="mini-player-volume-wrap">
        <button
          type="button"
          class="icon-btn h-9 w-9"
          :class="{ 'icon-btn-active': volumeOpen }"
          :title="t('player.volume')"
          :aria-label="t('player.volume')"
          :aria-expanded="volumeOpen"
          @click.stop="toggleVolume"
        >
          <Icon :icon="volumeIcon" class="h-5 w-5" />
        </button>
        <div
          v-if="volumeOpen"
          class="mini-player-volume"
          @click.stop
          @pointerdown.stop
        >
          <span class="mini-player-volume-value">{{ volumePercent }}%</span>
          <div class="mini-player-volume-shell">
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              :value="player.isMuted.value ? 0 : player.volume.value"
              class="mini-player-volume-slider"
              :aria-label="t('player.volume')"
              @input="onVolume"
            />
          </div>
        </div>
      </div>
      <button
        type="button"
        class="icon-btn h-9 w-9"
        :title="playbackActive ? t('player.pause') : t('player.play')"
        @click.stop="player.toggle()"
      >
        <Icon
          :icon="
            playbackActive ? 'clarity:pause-solid' : 'clarity:play-solid'
          "
          class="h-5 w-5"
        />
      </button>
      <button
        type="button"
        class="icon-btn h-9 w-9"
        :title="t('player.next')"
        @click.stop="player.next()"
      >
        <Icon icon="clarity:step-forward-2-line" class="h-5 w-5" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Icon } from '@iconify/vue'

import CoverImage from './CoverImage.vue'
import router from '../router'
import API from '../model/api'
import { usePlayer } from '../model/player'
import { useI18n } from '../i18n'

const route = useRoute()
const player = usePlayer()
const { t } = useI18n()
const volumeOpen = ref(false)
const volumeRoot = ref(null)
let swipeX = null
let skipOpenOnClick = false

const visible = computed(
  () => Boolean(player.currentTrack.value) && route.name !== 'Player'
)

watch(visible, (isVisible) => {
  if (!isVisible) volumeOpen.value = false
})

const playbackActive = computed(
  () => player.playbackIntent.value || player.isPlaying.value
)

const title = computed(
  () => player.currentTrack.value?.title || t('player.nowPlaying')
)
const artist = computed(() => player.currentTrack.value?.artist || '')
const cover = computed(() =>
  API.coverSourcesForNowPlaying(player.currentTrack.value?.file || '', {
    artistName: player.currentTrack.value?.artist || '',
  })
)
const volumeIcon = computed(() => {
  if (player.isMuted.value || player.volume.value === 0) {
    return 'clarity:volume-mute-line'
  }
  return player.volume.value < 0.5
    ? 'clarity:volume-down-line'
    : 'clarity:volume-up-line'
})
const volumePercent = computed(() =>
  player.isMuted.value ? 0 : Math.round((player.volume.value || 0) * 100)
)

function openPlayer() {
  if (skipOpenOnClick) {
    skipOpenOnClick = false
    return
  }
  volumeOpen.value = false
  router.push({ name: 'Player' })
}

function toggleVolume() {
  volumeOpen.value = !volumeOpen.value
}

function onVolume(event) {
  player.setVolume(Number(event.target.value))
}

function onDocumentPointerDown(event) {
  if (!volumeOpen.value) return
  const root = volumeRoot.value
  if (root && root.contains(event.target)) return
  volumeOpen.value = false
}

function onDocumentKeydown(event) {
  if (event.key === 'Escape') volumeOpen.value = false
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown)
  document.addEventListener('keydown', onDocumentKeydown)
})
onUnmounted(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  document.removeEventListener('keydown', onDocumentKeydown)
})

function onPointerDown(event) {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  swipeX = event.clientX
}

function onPointerUp(event) {
  if (swipeX == null) return
  const dx = event.clientX - swipeX
  swipeX = null
  if (Math.abs(dx) < 56) return
  skipOpenOnClick = true
  if (dx < 0) player.next()
  else player.prev()
}
</script>

<style scoped>
.mini-player {
  position: fixed;
  left: 0.75rem;
  right: 0.75rem;
  bottom: calc(var(--app-bottom-nav-height) + var(--app-safe-bottom) + 0.4rem);
  z-index: 45;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-radius: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: color-mix(in srgb, var(--b1) 88%, transparent);
  padding: 0.45rem 0.55rem;
  box-shadow: 0 12px 40px -16px rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(18px);
  overflow: visible;
  touch-action: pan-y;
}

.mini-player-main {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: 0.7rem;
}

.mini-player-cover {
  display: flex;
  height: 2.75rem;
  width: 2.75rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.06);
}

.mini-player-actions {
  display: flex;
  flex-shrink: 0;
  align-items: center;
}

.mini-player-volume-wrap {
  position: relative;
}

.mini-player-volume {
  position: absolute;
  right: 50%;
  bottom: calc(100% + 0.45rem);
  z-index: 50;
  display: flex;
  width: 3.25rem;
  transform: translateX(50%);
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  border-radius: 1.15rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: color-mix(in srgb, var(--b1) 94%, transparent);
  padding: 0.7rem 0.55rem 0.85rem;
  box-shadow: 0 12px 32px -16px rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(18px);
}

.mini-player-volume-value {
  font-size: 0.65rem;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  color: color-mix(in srgb, var(--bc) 70%, transparent);
}

.mini-player-volume-shell {
  display: flex;
  height: 5.5rem;
  width: 1.75rem;
  align-items: center;
  justify-content: center;
}

.mini-player-volume-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 5.5rem;
  height: 0.28rem;
  margin: 0;
  cursor: pointer;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  outline: none;
  transform: rotate(-90deg);
  transform-origin: center;
}

[data-theme='downtify-light'] .mini-player-volume-slider {
  background: rgba(0, 0, 0, 0.12);
}

.mini-player-volume-slider::-webkit-slider-runnable-track {
  height: 0.28rem;
  border-radius: 999px;
  background: transparent;
}

.mini-player-volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 0.85rem;
  height: 0.85rem;
  margin-top: -0.28rem;
  cursor: pointer;
  border-radius: 999px;
  background: #1ad05c;
  box-shadow: 0 0 10px rgba(26, 208, 92, 0.45);
}

.mini-player-volume-slider::-moz-range-track {
  height: 0.28rem;
  border-radius: 999px;
  background: transparent;
}

.mini-player-volume-slider::-moz-range-thumb {
  width: 0.85rem;
  height: 0.85rem;
  cursor: pointer;
  border: none;
  border-radius: 999px;
  background: #1ad05c;
  box-shadow: 0 0 10px rgba(26, 208, 92, 0.45);
}

@media (min-width: 1024px) {
  .mini-player {
    left: auto;
    right: 1.25rem;
    bottom: 1.25rem;
    width: min(28rem, calc(100vw - 2.5rem));
  }
}
</style>
