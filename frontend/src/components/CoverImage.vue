<template>
  <div class="contents">
    <img
      v-show="imageReady && displaySrc && !failed"
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
      ref="rootRef"
      v-show="!imageReady || !displaySrc || failed"
      :class="imgClass"
      class="flex items-center justify-center"
    >
      <slot name="fallback" />
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

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
  eager: {
    type: Boolean,
    default: false,
  },
})

const displaySrc = ref('')
const failed = ref(false)
const imageReady = ref(false)
const restoredFromCache = ref(false)
const rootRef = ref(null)
const isNearViewport = ref(false)
let requestId = 0
let candidateUrls = []
let candidateIndex = 0
let observer = null
let imageLoadTimer = 0

const sourceKey = computed(() =>
  buildCoverSourceKey(props.src, props.fallbacks)
)

const imageLoading = computed(() =>
  props.eager ||
  usesEmbeddedServer() ||
  restoredFromCache.value ||
  displaySrc.value
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
  imageReady.value = Boolean(cached.displaySrc && !cached.failed)
  restoredFromCache.value = Boolean(cached.displaySrc && !cached.failed)
  return restoredFromCache.value
}

function retryLoad() {
  if (!sourceKey.value) return
  failed.value = false
  imageReady.value = false
  restoredFromCache.value = false
  resetCandidates(props.src, props.fallbacks)
  if (shouldLoadNow.value) void loadCurrentCandidate()
}

function handleEmbeddedServerReady() {
  if (!usesEmbeddedServer()) return
  if (!sourceKey.value) return
  const cached = getCachedCoverDisplay(sourceKey.value)
  if (failed.value || cached?.failed || (!displaySrc.value && !failed.value)) {
    retryLoad()
  }
}

async function applyCandidate(url) {
  if (!url) return false
  const current = ++requestId
  failed.value = false
  imageReady.value = false

  const resolved = await resolveImageSrc(url)
  if (current !== requestId) return true
  if (!resolved) {
    onError()
    return false
  }

  displaySrc.value = resolved
  window.clearTimeout(imageLoadTimer)
  imageLoadTimer = window.setTimeout(() => {
    if (current === requestId) onError()
  }, 20000)
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
  window.clearTimeout(imageLoadTimer)
  imageLoadTimer = 0
  imageReady.value = true
  rememberCoverDisplay(sourceKey.value, displaySrc.value, false)
  restoredFromCache.value = true
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
    imageReady.value = false
    rememberCoverDisplay(sourceKey.value, '', true)
    return
  }
  await applyCandidate(url)
}

const shouldLoadNow = computed(
  () => props.eager || isNearViewport.value || restoredFromCache.value
)

function observeVisibility() {
  if (isNearViewport.value) return
  if (typeof IntersectionObserver === 'undefined') {
    isNearViewport.value = true
    return
  }

  const target = rootRef.value
  if (!target) return

  observer = new IntersectionObserver(
    (entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return
      isNearViewport.value = true
      observer?.disconnect()
      observer = null
    },
    { root: null, rootMargin: '700px 0px', threshold: 0.01 }
  )
  observer.observe(target)
}

function onError() {
  window.clearTimeout(imageLoadTimer)
  imageLoadTimer = 0
  if (candidateIndex < candidateUrls.length - 1) {
    candidateIndex += 1
    displaySrc.value = ''
    imageReady.value = false
    void applyCandidate(candidateUrls[candidateIndex])
    return
  }
  failed.value = true
  displaySrc.value = ''
  imageReady.value = false
  rememberCoverDisplay(sourceKey.value, '', true)
}

watch(
  sourceKey,
  (key, previousKey) => {
    if (!key) {
      failed.value = true
      displaySrc.value = ''
      imageReady.value = false
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
      imageReady.value = false
      restoredFromCache.value = false
    }

    if (shouldLoadNow.value) void loadCurrentCandidate()
  },
  { immediate: true }
)

watch(shouldLoadNow, (ready) => {
  if (!ready || displaySrc.value || failed.value || !sourceKey.value) return
  void loadCurrentCandidate()
})

onMounted(() => {
  void nextTick(observeVisibility)
  if (usesEmbeddedServer()) {
    window.addEventListener(
      EMBEDDED_SERVER_READY_EVENT,
      handleEmbeddedServerReady
    )
  }
})

onUnmounted(() => {
  window.clearTimeout(imageLoadTimer)
  observer?.disconnect()
  window.removeEventListener(
    EMBEDDED_SERVER_READY_EVENT,
    handleEmbeddedServerReady
  )
})
</script>
