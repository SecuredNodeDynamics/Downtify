<template>
  <span
    v-if="entry"
    class="library-browse-card-monitor"
    :class="{ 'library-browse-card-monitor-paused': !entry.enabled }"
    :title="
      entry.enabled ? t('library.monitoringArtist') : t('library.monitorPaused')
    "
    aria-hidden="true"
  >
    <Icon
      :icon="entry.enabled ? 'clarity:eye-solid' : 'clarity:eye-line'"
      class="h-3.5 w-3.5"
    />
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

import { useI18n } from '../i18n'
import { findMonitoredArtist, monitoredArtists } from '../model/monitoredArtists'

const props = defineProps({
  artistName: {
    type: String,
    required: true,
  },
})

const { t } = useI18n()

const entry = computed(() => {
  monitoredArtists.value
  return findMonitoredArtist(props.artistName)
})
</script>

<style scoped>
.library-browse-card-monitor {
  @apply pointer-events-none absolute right-2 top-2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-primary text-primary-content shadow-glow-sm;
}

.library-browse-card-monitor-paused {
  @apply border border-white/15 bg-base-100/90 text-base-content/55 shadow-none;
}
</style>
