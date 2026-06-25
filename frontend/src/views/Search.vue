<template>
  <div class="min-h-0 overflow-x-hidden">
    <Navbar />
    <SearchList
      :data="filteredResults"
      :error="sm.error.value"
      @download="(song) => dm.queue(song)"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

import { useSearchManager } from '../model/search'
import { useDownloadManager } from '../model/download'
import { resolveSearchRouteQuery } from '../model/searchNavigation'
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

const searchQuery = computed(() => resolveSearchRouteQuery(route))
const filteredResults = computed(() => sm.filteredResults.value)

function runSearch() {
  const query = searchQuery.value
  if (query) sm.searchFor(query)
}

watch(searchQuery, runSearch)

runSearch()
</script>
