<template>
  <div class="contents">
    <img
      v-show="displaySrc && !failed"
      :src="displaySrc"
      :alt="alt"
      :class="imgClass"
      referrerpolicy="no-referrer"
      loading="lazy"
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

import { resolveNativeImageSrc } from '../model/imageLoader'

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
let requestId = 0
let candidateUrls = []
let candidateIndex = 0

const sourceKey = computed(() =>
  [props.src, ...(props.fallbacks || [])]
    .map((url) => String(url || '').trim())
    .filter(Boolean)
    .join('\0')
)

function resetCandidates(primary, fallbacks = []) {
  candidateUrls = [primary, ...fallbacks]
    .map((url) => String(url || '').trim())
    .filter(Boolean)
  candidateIndex = 0
}

async function applyCandidate(url) {
  if (!url) return false
  const current = ++requestId
  failed.value = false

  const resolved = await resolveNativeImageSrc(url)
  if (current !== requestId) return true

  displaySrc.value = resolved || url
  return true
}

async function loadCurrentCandidate() {
  const url = candidateUrls[candidateIndex]
  if (!url) {
    failed.value = true
    return
  }
  await applyCandidate(url)
}

function onError() {
  if (candidateIndex < candidateUrls.length - 1) {
    candidateIndex += 1
    const nextUrl = candidateUrls[candidateIndex]
    displaySrc.value = nextUrl
    void applyCandidate(nextUrl)
    return
  }
  failed.value = true
}

watch(
  sourceKey,
  (key, previousKey) => {
    if (!key) {
      failed.value = true
      displaySrc.value = ''
      candidateUrls = []
      candidateIndex = 0
      return
    }
    resetCandidates(props.src, props.fallbacks)
    if (previousKey && previousKey !== key) {
      displaySrc.value = ''
      failed.value = false
    }
    void loadCurrentCandidate()
  },
  { immediate: true }
)
</script>
