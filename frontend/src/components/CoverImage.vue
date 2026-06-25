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
      @load="onImageLoad"
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
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import { EMBEDDED_SERVER_READY_EVENT } from '../model/embeddedServer'
import {
  buildCoverSourceKey,
  canLoadImageDirectly,
  getCachedCoverDisplay,
  persistLoadedImage,
  rememberCoverDisplay,
  resolveImageSrc,
} from '../model/imageLoader'
import { usesEmbeddedServer } from '../model/serverConnection'

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
  usesEmbeddedServer() || restoredFromCache.value || displaySrc.value
    ? 'eager'
    : 'lazy'
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

  if (cached.failed) {
    restoredFromCache.value = false
    return false
  }

  displaySrc.value = cached.displaySrc
  failed.value = cached.failed
  restoredFromCache.value = Boolean(cached.displaySrc && !cached.failed)
  return restoredFromCache.value
}

function retryLoad() {
  if (!sourceKey.value) return
  failed.value = false
  restoredFromCache.value = false
  resetCandidates(props.src, props.fallbacks)
  void loadCurrentCandidate()
}

function handleEmbeddedServerReady() {
  if (!usesEmbeddedServer()) return
  if (!sourceKey.value) return
  const cached = getCachedCoverDisplay(sourceKey.value)
  if (cached?.failed || (!displaySrc.value && !failed.value)) {
    retryLoad()
  }
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

  if (canLoadImageDirectly(url) && !displaySrc.value.startsWith('blob:')) {
    void persistLoadedImage(url).then((upgraded) => {
      if (!upgraded?.startsWith('blob:') || current !== requestId) return
      displaySrc.value = upgraded
      rememberCoverDisplay(sourceKey.value, upgraded, false)
    })
  }

  return true
}

function onImageLoad() {
  const url = candidateUrls[candidateIndex]
  if (
    url &&
    canLoadImageDirectly(url) &&
    !displaySrc.value.startsWith('blob:')
  ) {
    void persistLoadedImage(url)
  }
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

onMounted(() => {
  if (usesEmbeddedServer()) {
    window.addEventListener(
      EMBEDDED_SERVER_READY_EVENT,
      handleEmbeddedServerReady
    )
  }
})

onUnmounted(() => {
  window.removeEventListener(
    EMBEDDED_SERVER_READY_EVENT,
    handleEmbeddedServerReady
  )
})
</script>
