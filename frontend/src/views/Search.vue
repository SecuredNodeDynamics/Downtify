<template>
  <div class="min-h-0 overflow-x-hidden">
    <Navbar />
    <SearchList
      :data="filteredResults"
      :error="sm.error.value || downloadError"
      @download="onDownload"
    />
  </div>
</template>

<script setup>
defineOptions({ name: 'Search' })
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { useSearchManager } from '../model/search'
import { useDownloadManager } from '../model/download'
import { resolveSearchRouteQuery } from '../model/searchNavigation'
import { useI18n } from '../i18n'
import API from '../model/api'

import Navbar from '/src/components/Navbar.vue'
import SearchList from '/src/components/SearchList.vue'

onMounted(() => {
  window.scroll(0, 0)
  void API.refreshLibraryInBackground()
})

const route = useRoute()
const sm = useSearchManager()
const dm = useDownloadManager()
const { t } = useI18n()
const downloadError = ref('')

const searchQuery = computed(() => resolveSearchRouteQuery(route))
const filteredResults = computed(() => sm.filteredResults.value)

function runSearch() {
  const query = searchQuery.value
  if (query) sm.searchFor(query)
}

function onDownload(song) {
  downloadError.value = ''
  void dm.queue(song).then((result) => {
    if (result?.failed) {
      downloadError.value = result.error || t('search.queueAlbumFailed')
    }
  })
}

watch(searchQuery, runSearch)

runSearch()
</script>
