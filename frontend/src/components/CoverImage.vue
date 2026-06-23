<template>
  <img
    v-if="displaySrc && !failed"
    :src="displaySrc"
    :alt="alt"
    :class="imgClass"
    referrerpolicy="no-referrer"
    loading="lazy"
    @error="onError"
  />
  <slot v-else name="fallback" />
</template>

<script setup>
import { ref, watch } from 'vue'

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

function resetCandidates(primary, fallbacks = []) {
  candidateUrls = [primary, ...fallbacks]
    .map((url) => String(url || '').trim())
    .filter(Boolean)
  candidateIndex = 0
}

async function loadCandidate(url) {
  const current = ++requestId
  failed.value = false
  displaySrc.value = ''

  const resolved = await resolveNativeImageSrc(url)
  if (current !== requestId) return
  displaySrc.value = resolved || url
}

async function loadCurrentCandidate() {
  const url = candidateUrls[candidateIndex]
  if (!url) {
    failed.value = true
    displaySrc.value = ''
    return
  }
  await loadCandidate(url)
}

function onError() {
  if (candidateIndex < candidateUrls.length - 1) {
    candidateIndex += 1
    loadCurrentCandidate()
    return
  }
  failed.value = true
}

watch(
  () => [props.src, props.fallbacks],
  () => {
    resetCandidates(props.src, props.fallbacks)
    loadCurrentCandidate()
  },
  { immediate: true, deep: true }
)
</script>
