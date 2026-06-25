<template>
  <SearchField
    root-class="w-full"
    :model-value="sm.searchTerm.value"
    :placeholder="placeHolder"
    :size="compact ? 'compact' : 'large'"
    :submit-icon="'search'"
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
import { buildSearchRoute } from '../model/searchNavigation'
import { useI18n } from '../i18n'
import SearchField from './SearchField.vue'

defineProps({
  compact: { type: Boolean, default: false },
})

const sm = useSearchManager()
const dm = useDownloadManager()
const { t, locale } = useI18n()

const placeHolderKeys = [
  'search.placeholderArtist',
  'search.placeholderAlbum',
  'search.placeholderTrack',
]
const rotationIndex = ref(0)
const placeHolder = computed(() => {
  const _ = locale.value
  return t(placeHolderKeys[rotationIndex.value])
})

const canSubmit = computed(() => {
  const query = sm.searchTerm.value?.trim()
  if (!query) return false
  return sm.isValidSearch(query) || sm.isValidURL(query)
})

const polling = setInterval(() => {
  rotationIndex.value = (rotationIndex.value + 1) % placeHolderKeys.length
}, 5000)
onBeforeUnmount(() => clearInterval(polling))

function lookUp(query) {
  const trimmed = query?.trim()
  if (!trimmed) return
  if (!sm.isValidSearch(trimmed) && !sm.isValidURL(trimmed)) return
  router.push(buildSearchRoute(trimmed))
}
</script>
