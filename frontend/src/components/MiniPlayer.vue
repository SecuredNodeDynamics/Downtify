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
      <button
        type="button"
        class="icon-btn h-9 w-9"
        :title="t('player.volume')"
        @click.stop="volumeOpen = !volumeOpen"
      >
        <Icon :icon="volumeIcon" class="h-5 w-5" />
      </button>
      <button
        type="button"
        class="icon-btn h-9 w-9"
        :title="player.isPlaying.value ? t('player.pause') : t('player.play')"
        @click.stop="player.toggle()"
      >
        <Icon
          :icon="
            player.isPlaying.value ? 'clarity:pause-solid' : 'clarity:play-solid'
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

    <div v-if="volumeOpen" class="mini-player-volume" @click.stop>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        :value="player.isMuted.value ? 0 : player.volume.value"
        :aria-label="t('player.volume')"
        @input="onVolume"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
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
let swipeX = null

const visible = computed(
  () => Boolean(player.currentTrack.value) && route.name !== 'Player'
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

function openPlayer() {
  volumeOpen.value = false
  router.push({ name: 'Player' })
}

function onVolume(event) {
  player.setVolume(Number(event.target.value))
}

function onPointerDown(event) {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  swipeX = event.clientX
}

function onPointerUp(event) {
  if (swipeX == null) return
  const dx = event.clientX - swipeX
  swipeX = null
  if (Math.abs(dx) < 56) return
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

.mini-player-volume {
  position: absolute;
  right: 0.75rem;
  bottom: calc(100% + 0.4rem);
  width: 9rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: color-mix(in srgb, var(--b1) 92%, transparent);
  padding: 0.55rem 0.75rem;
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
