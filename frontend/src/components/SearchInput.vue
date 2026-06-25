<template>
  <SearchField
    root-class="w-full"
    :model-value="sm.searchTerm.value"
    :placeholder="placeHolder"
    :size="compact ? 'compact' : 'large'"
    :submit-icon="sm.isValidURL(sm.searchTerm.value) ? 'download' : 'search'"
    :submit-disabled="dm.loading.value || !canSubmit"
    :submit-loading="dm.loading.value"
    @update:model-value="sm.searchTerm.value = $event"
    @submit="lookUp(sm.searchTerm.value)"
  />
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'

import router from '../router'
import { useSearchManager } from '../model/search'
import { useDownloadManager } from '../model/download'
import { useI18n } from '../i18n'
import SearchField from './SearchField.vue'

defineProps({
  compact: { type: Boolean, default: false },
})

const sm = useSearchManager()
const dm = useDownloadManager()
const { t, locale } = useI18n()

const placeHolderRotation = [
  'https://open.spotify.com/track/4vfN00PlILRXy5dcXHQE9M',
  'drugs - EDEN',
  'Não Gosto Eu Amo - Henrique e Juliano',
  'Perfect - Ed Sheeran',
  'Lightning Crashes - Live',
]
const rotationIndex = ref(0)
const placeHolder = computed(() => {
  const _ = locale.value
  if (rotationIndex.value === 0) return t('search.placeholder')
  return placeHolderRotation[rotationIndex.value - 1]
})

const canSubmit = computed(() => {
  const query = sm.searchTerm.value?.trim()
  if (!query) return false
  return sm.isValidSearch(query) || sm.isValidURL(query)
})

const polling = setInterval(() => {
  rotationIndex.value =
    (rotationIndex.value + 1) % (placeHolderRotation.length + 1)
}, 5000)
onBeforeUnmount(() => clearInterval(polling))

function lookUp(query) {
  if (!query || !query.trim()) return
  if (sm.isValidURL(query)) {
    dm.fromURL(query)
    router.push({ name: 'Download' })
  } else if (sm.isValidSearch(query)) {
    router.push({ name: 'Search', params: { query } })
  }
}
</script>
