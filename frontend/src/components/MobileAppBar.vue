<template>
  <header class="mobile-app-bar lg:hidden">
    <div class="mobile-app-bar-inner safe-top">
      <button
        v-if="showBack"
        type="button"
        class="mobile-app-bar-icon"
        :title="t('nav.back')"
        @click="goBack"
      >
        <Icon icon="clarity:arrow-line" class="h-6 w-6 rotate-90" />
      </button>
      <button
        v-else
        type="button"
        class="mobile-app-bar-logo"
        :title="t('nav.home')"
        @click="router.push({ name: 'Home' })"
      >
        <img
          src="../assets/downtify.svg"
          class="h-7 w-7 drop-shadow-[0_0_8px_rgba(26,208,92,0.55)]"
          alt=""
        />
      </button>

      <h1 class="mobile-app-bar-title truncate">{{ pageTitle }}</h1>

      <div class="ml-auto flex shrink-0 items-center gap-1">
        <label
          for="settings-modal"
          class="mobile-app-bar-icon cursor-pointer"
          :title="t('nav.settings')"
        >
          <Icon icon="clarity:cog-line" class="h-5 w-5" />
        </label>
      </div>
    </div>

    <div v-if="showSearchBar" class="mobile-app-bar-search safe-top">
      <SearchInput :compact="true" />
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'

import router from '../router'
import { useI18n } from '../i18n'
import SearchInput from './SearchInput.vue'

const route = useRoute()
const { t } = useI18n()

const primaryRoutes = new Set(['Home', 'List', 'Download', 'Player'])

const showBack = computed(() => {
  if (route.name === 'Search') return true
  return route.name && !primaryRoutes.has(route.name)
})

const showSearchBar = computed(() => route.name === 'Search')

const pageTitle = computed(() => {
  const key = route.meta?.mobileTitleKey
  if (key) return t(key)
  if (route.name === 'Search') return t('nav.search')
  return 'Downtify'
})

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push({ name: 'Home' })
}
</script>
