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
      </span>
      <span class="bottom-nav-label">{{ t(item.labelKey) }}</span>
    </button>
  </nav>
</template>

<script setup>
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'

import router from '../router'
import { useMobileSearch } from '../model/mobileSearch'
import { useI18n } from '../i18n'

const route = useRoute()
const mobileSearch = useMobileSearch()
const { t } = useI18n()

const items = [
  { name: 'Home', labelKey: 'nav.home', icon: 'clarity:home-line' },
  { name: 'List', labelKey: 'nav.library', icon: 'clarity:library-line' },
  { name: 'Player', labelKey: 'nav.player', icon: 'clarity:headphones-line' },
  { name: 'Search', labelKey: 'nav.search', icon: 'clarity:search-line' },
  {
    name: 'More',
    labelKey: 'nav.more',
    icon: 'clarity:ellipsis-horizontal-line',
  },
]

const moreRoutes = new Set(['Monitor', 'Health', 'Metadata', 'Download'])

function isActive(item) {
  if (item.name === 'More') {
    return moreRoutes.has(route.name)
  }
  if (item.name === 'Home') {
    return route.name === 'Home'
  }
  if (item.name === 'Search') {
    return route.name === 'Search'
  }
  return route.name === item.name
}

function onNav(item) {
  if (item.name === 'More') {
    const sheet = document.getElementById('mobile-more-sheet')
    if (sheet) sheet.checked = true
    return
  }
  if (item.name === 'Search') {
    mobileSearch.openSheetAndFocus()
    return
  }
  router.push({ name: item.name })
}
</script>
