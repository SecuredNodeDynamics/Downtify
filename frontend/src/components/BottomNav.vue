<template>
  <nav class="bottom-nav lg:hidden" aria-label="Main navigation">
    <button
      v-for="item in items"
      :key="item.name"
      type="button"
      class="bottom-nav-item"
      :class="{ 'bottom-nav-item-active': isActive(item) }"
      :title="t(item.labelKey)"
      @click="onNav(item)"
    >
      <span class="bottom-nav-icon-wrap">
        <Icon :icon="item.icon" class="h-6 w-6" />
        <span
          v-if="item.name === 'Download' && pt.activeDownloadCount.value > 0"
          class="bottom-nav-badge"
        >
          {{ pt.activeDownloadCount.value }}
        </span>
      </span>
      <span class="bottom-nav-label">{{ t(item.labelKey) }}</span>
    </button>
  </nav>
</template>

<script setup>
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'

import router from '../router'
import { useProgressTracker } from '../model/download'
import { useI18n } from '../i18n'

const route = useRoute()
const pt = useProgressTracker()
const { t } = useI18n()

const items = [
  { name: 'Home', labelKey: 'nav.home', icon: 'clarity:home-line' },
  { name: 'List', labelKey: 'nav.library', icon: 'clarity:library-line' },
  { name: 'Download', labelKey: 'nav.queue', icon: 'clarity:download-line' },
  { name: 'Player', labelKey: 'nav.player', icon: 'clarity:headphones-line' },
  { name: 'More', labelKey: 'nav.more', icon: 'clarity:ellipsis-horizontal-line' },
]

const moreRoutes = new Set(['Monitor', 'Health', 'Metadata'])

function isActive(item) {
  if (item.name === 'More') {
    return moreRoutes.has(route.name)
  }
  if (item.name === 'Home') {
    return route.name === 'Home' || route.name === 'Search'
  }
  return route.name === item.name
}

function onNav(item) {
  if (item.name === 'More') {
    const sheet = document.getElementById('mobile-more-sheet')
    if (sheet) sheet.checked = true
    return
  }
  router.push({ name: item.name })
}
</script>
