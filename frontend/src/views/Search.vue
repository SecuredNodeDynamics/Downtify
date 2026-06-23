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

import Navbar from '/src/components/Navbar.vue'
import SearchList from '/src/components/SearchList.vue'

onMounted(() => window.scroll(0, 0))

const route = useRoute()
const sm = useSearchManager()
const dm = useDownloadManager()

const filteredResults = computed(() => sm.filterResults(sm.results.value))

watch(
  () => route.params.query,
  () => {
    if (route.params.query) sm.searchFor(route.params.query)
  },
  { deep: true }
)

sm.searchFor(route.params.query)
</script>
