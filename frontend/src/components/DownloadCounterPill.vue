<template>
  <button
    v-if="pt.activeDownloadCount.value > 0"
    type="button"
    class="download-counter-pill"
    :class="{ 'download-counter-pill-compact': compact }"
    :title="t('nav.downloadCounter', { count: pt.activeDownloadCount.value })"
    @click="router.push({ name: 'Download' })"
  >
    <Icon icon="clarity:download-line" class="h-4 w-4 shrink-0" />
    <span class="tabular-nums font-semibold">{{
      pt.activeDownloadCount.value
    }}</span>
  </button>
</template>

<script setup>
import { Icon } from '@iconify/vue'

import router from '../router'
import { useProgressTracker } from '../model/download'
import { useI18n } from '../i18n'

defineProps({
  compact: { type: Boolean, default: false },
})

const pt = useProgressTracker()
const { t } = useI18n()
</script>

<style scoped>
.download-counter-pill {
  @apply inline-flex h-9 shrink-0 items-center gap-1.5 rounded-full border border-primary/25 bg-primary/15 px-3 text-sm font-medium text-primary shadow-glow-sm transition-colors hover:bg-primary/20 active:bg-primary/25;
}

.download-counter-pill-compact {
  @apply h-8 px-2.5 text-xs;
}
</style>
