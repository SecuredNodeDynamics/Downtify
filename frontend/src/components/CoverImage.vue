<template>
  <div class="contents">
    <img
      v-show="displaySrc && !failed"
      :src="displaySrc"
      :alt="alt"
      :class="imgClass"
      referrerpolicy="no-referrer"
      :loading="imageLoading"
      decoding="async"
      @error="onError"
    />
    <div
      v-show="!displaySrc || failed"
      :class="imgClass"
      class="flex items-center justify-center"
    >
      <slot name="fallback" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import {
  buildCoverSourceKey,
  getCachedCoverDisplay,
  rememberCoverDisplay,
  resolveImageSrc,
} from '../model/imageLoader'

const props = defineProps({
  src: {
    type: String,
    default: '',
  },
  fallbacks: {
    type: Array,
    default: () => [],
  },
  alt: {
    type: String,
    default: '',
  },
  imgClass: {
    type: String,
    default: '',
  },
})

const displaySrc = ref('')
const failed = ref(false)
const restoredFromCache = ref(false)
let requestId = 0
let candidateUrls = []
let candidateIndex = 0

const sourceKey = computed(() =>
  buildCoverSourceKey(props.src, props.fallbacks)
)

const imageLoading = computed(() =>
  restoredFromCache.value || displaySrc.value ? 'eager' : 'lazy'
)

function resetCandidates(primary, fallbacks = []) {
  candidateUrls = [primary, ...fallbacks]
    .map((url) => String(url || '').trim())
    .filter(Boolean)
  candidateIndex = 0
}

function restoreFromCache(key) {
  const cached = getCachedCoverDisplay(key)
  if (!cached) {
    restoredFromCache.value = false
    return false
  }

  displaySrc.value = cached.displaySrc
  failed.value = cached.failed
  restoredFromCache.value = Boolean(cached.displaySrc && !cached.failed)
  return restoredFromCache.value || cached.failed
}

async function applyCandidate(url) {
  if (!url) return false
  const current = ++requestId
  failed.value = false

  const resolved = await resolveImageSrc(url)
  if (current !== requestId) return true

  displaySrc.value = resolved || url
  rememberCoverDisplay(sourceKey.value, displaySrc.value, false)
  restoredFromCache.value = true
  return true
}

async function loadCurrentCandidate() {
  const url = candidateUrls[candidateIndex]
  if (!url) {
    failed.value = true
    rememberCoverDisplay(sourceKey.value, '', true)
    return
  }
  await applyCandidate(url)
}

function onError() {
  if (candidateIndex < candidateUrls.length - 1) {
    candidateIndex += 1
    displaySrc.value = ''
    void applyCandidate(candidateUrls[candidateIndex])
    return
  }
  failed.value = true
  displaySrc.value = ''
  rememberCoverDisplay(sourceKey.value, '', true)
}

watch(
  sourceKey,
  (key, previousKey) => {
    if (!key) {
      failed.value = true
      displaySrc.value = ''
      restoredFromCache.value = false
      candidateUrls = []
      candidateIndex = 0
      return
    }

    resetCandidates(props.src, props.fallbacks)

    if (restoreFromCache(key)) {
      return
    }

    if (previousKey && previousKey !== key) {
      displaySrc.value = ''
      failed.value = false
      restoredFromCache.value = false
    }

    void loadCurrentCandidate()
  },
  { immediate: true }
)
</script>
