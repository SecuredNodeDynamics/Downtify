<template>
  <div class="genre-cover" :style="baseStyle">
    <div
      v-if="coverFiles.length"
      class="genre-cover-mosaic"
      :class="mosaicClass"
    >
      <div
        v-for="file in coverFiles"
        :key="file"
        class="genre-cover-tile"
      >
        <CoverImage
          :key="file"
          :src="coverSourceFor(file).src"
          :fallbacks="coverSourceFor(file).fallbacks"
          :alt="name"
          img-class="absolute inset-0 h-full w-full object-cover"
        >
          <template #fallback>
            <div class="genre-cover-tile-fallback" :style="tileFallbackStyle" />
          </template>
        </CoverImage>
      </div>
    </div>
    <div
      class="genre-cover-overlay"
      :class="{ 'genre-cover-overlay-strong': !coverFiles.length }"
      :style="overlayStyle"
    />
    <Icon
      v-if="!coverFiles.length"
      :icon="icon"
      class="genre-cover-icon"
      aria-hidden="true"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

import CoverImage from '/src/components/CoverImage.vue'
import API from '/src/model/api'
import {
  genreCoverIcon,
  genreCoverStyle,
  genreOverlayStyle,
} from '/src/model/genreArt'

const props = defineProps({
  name: {
    type: String,
    default: '',
  },
  files: {
    type: Array,
    default: () => [],
  },
})

const coverFiles = computed(() =>
  (props.files || []).map((file) => String(file || '').trim()).filter(Boolean)
)

const coverSourceMap = computed(() => {
  const map = new Map()
  for (const file of coverFiles.value) {
    map.set(file, API.coverSourcesForFile(file))
  }
  return map
})

function coverSourceFor(file) {
  return coverSourceMap.value.get(file) || API.coverSourcesForFile(file)
}

const mosaicClass = computed(() => {
  const count = coverFiles.value.length
  if (count <= 1) return 'genre-cover-mosaic-1'
  if (count === 2) return 'genre-cover-mosaic-2'
  if (count === 3) return 'genre-cover-mosaic-3'
  return 'genre-cover-mosaic-4'
})

const baseStyle = computed(() =>
  coverFiles.value.length ? {} : genreCoverStyle(props.name)
)

const overlayStyle = computed(() => genreOverlayStyle(props.name))

const tileFallbackStyle = computed(() => genreCoverStyle(props.name))

const icon = computed(() => genreCoverIcon(props.name))
</script>

<style scoped>
.genre-cover {
  @apply relative h-full w-full overflow-hidden bg-primary/10;
}

.genre-cover-mosaic {
  @apply absolute inset-0 grid gap-px bg-black/20;
}

.genre-cover-mosaic-1 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}

.genre-cover-mosaic-2 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr;
}

.genre-cover-mosaic-3 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.genre-cover-mosaic-3 .genre-cover-tile:first-child {
  grid-row: span 2;
}

.genre-cover-mosaic-4 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.genre-cover-tile {
  @apply relative overflow-hidden bg-base-300/40;
}

.genre-cover-tile-fallback {
  @apply absolute inset-0;
}

.genre-cover-overlay {
  @apply pointer-events-none absolute inset-0 mix-blend-multiply;
}

.genre-cover-overlay-strong {
  opacity: 0.18 !important;
  mix-blend-mode: normal;
}

.genre-cover-icon {
  @apply absolute left-1/2 top-1/2 h-10 w-10 -translate-x-1/2 -translate-y-1/2 text-white/85 drop-shadow;
}
</style>
