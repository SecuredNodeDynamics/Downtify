<template>
  <div
    class="search-result-filter"
    role="group"
    :aria-label="t('search.filterLabel')"
  >
    <button
      v-for="option in options"
      :key="option.id"
      type="button"
      class="search-result-filter-btn"
      :class="
        sm.resultFilter.value === option.id
          ? 'bg-primary text-primary-content shadow-glow-sm'
          : 'text-base-content/60 hover:text-base-content'
      "
      @click="sm.setResultFilter(option.id)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import { useSearchManager } from '../model/search'
import { useI18n } from '../i18n'

const sm = useSearchManager()
const { t } = useI18n()

const options = computed(() => [
  { id: 'both', label: t('search.filterBoth') },
  { id: 'albums', label: t('search.filterAlbums') },
  { id: 'tracks', label: t('search.filterTracks') },
])
</script>

<style scoped>
.search-result-filter {
  @apply grid w-full grid-cols-3 gap-1 rounded-full border border-white/10 bg-base-100/75 p-1;
}

.search-result-filter-btn {
  @apply inline-flex w-full items-center justify-center rounded-full px-2 py-2.5 text-center text-xs font-medium leading-tight transition-colors sm:px-4 sm:py-2 sm:text-sm;
}
</style>
