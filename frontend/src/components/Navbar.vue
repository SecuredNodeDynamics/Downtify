<template>
  <header class="sticky top-0 z-30 glass-nav hidden lg:block">
    <div
      class="mx-auto flex h-16 w-full max-w-6xl items-center gap-3 px-4 sm:px-6"
    >
      <button
        class="flex items-center gap-2 shrink-0"
        @click="router.push({ name: 'Home' })"
        :title="t('nav.home')"
      >
        <img
          src="../assets/downtify.svg"
          class="h-8 w-8 drop-shadow-[0_0_8px_rgba(26,208,92,0.55)]"
        />
        <span class="hidden sm:inline text-lg font-bold tracking-tight">
          Downtify
        </span>
      </button>

      <div class="hidden md:flex flex-1 justify-center">
        <SearchInput class="w-full max-w-md" :compact="true" />
      </div>

      <div class="ml-auto flex items-center gap-2 sm:gap-3">
        <DownloadCounterPill />

        <div class="flex items-center gap-1 sm:gap-2">
          <button
            class="icon-btn"
            :class="{ 'icon-btn-active': route.name === 'List' }"
            @click="router.push({ name: 'List' })"
            :title="t('nav.library')"
          >
            <Icon icon="clarity:library-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            :class="{ 'icon-btn-active': route.name === 'Player' }"
            @click="router.push({ name: 'Player' })"
            :title="t('nav.player')"
          >
            <Icon icon="clarity:headphones-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            :class="{ 'icon-btn-active': route.name === 'Monitor' }"
            @click="router.push({ name: 'Monitor' })"
            :title="t('nav.monitor')"
          >
            <Icon icon="clarity:eye-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            :class="{ 'icon-btn-active': route.name === 'Health' }"
            @click="router.push({ name: 'Health' })"
            :title="t('nav.health')"
          >
            <Icon icon="clarity:info-standard-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            :class="{ 'icon-btn-active': route.name === 'Metadata' }"
            @click="router.push({ name: 'Metadata' })"
            :title="t('nav.metadata')"
          >
            <Icon icon="clarity:tag-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            :class="{ 'icon-btn-active': route.name === 'Download' }"
            @click="
              route.name === 'Download'
                ? router.push({
                    name: 'Search',
                    params: { query: sm.searchTerm.value || ' ' },
                  })
                : router.push({ name: 'Download' })
            "
            :title="t('nav.queue')"
          >
            <Icon icon="clarity:download-line" class="h-5 w-5" />
          </button>

          <button
            v-if="route.name === 'List'"
            type="button"
            class="icon-btn"
            :class="{ 'icon-btn-error': libraryRefreshFailed }"
            :title="t('common.refresh')"
            :disabled="libraryRefreshLoading"
            @click="refreshLibrary()"
          >
            <Icon
              icon="clarity:refresh-line"
              class="h-5 w-5 transition-colors"
              :class="[
                libraryRefreshLoading ? 'animate-spin text-primary' : '',
                libraryRefreshFailed ? 'text-error' : '',
              ]"
            />
          </button>

          <button
            v-if="route.name === 'Health'"
            class="icon-btn"
            :title="t('common.refresh')"
            :disabled="healthRefreshLoading"
            @click="refreshHealth()"
          >
            <span
              v-if="healthRefreshLoading"
              class="loading loading-spinner loading-sm text-primary"
            />
            <Icon v-else icon="clarity:refresh-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            @click="
              themeMgr.setTheme(
                themeMgr.currentTheme.value === 'dark' ? 'light' : 'dark'
              )
            "
            :title="
              themeMgr.currentTheme.value === 'dark'
                ? t('nav.switchToLight')
                : t('nav.switchToDark')
            "
          >
            <Icon
              v-if="themeMgr.currentTheme.value === 'dark'"
              icon="clarity:sun-line"
              class="h-5 w-5"
            />
            <Icon v-else icon="clarity:moon-line" class="h-5 w-5" />
          </button>

          <button
            type="button"
            class="icon-btn cursor-pointer"
            :title="t('nav.settings')"
            @click="openSettingsModal()"
          >
            <Icon icon="clarity:cog-line" class="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'

import router from '../router'
import { useBinaryThemeManager } from '../model/theme'
import { useSearchManager } from '../model/search'
import { useHealthRefresh } from '../model/healthRefresh'
import { useLibraryRefresh } from '../model/libraryRefresh'
import { useI18n } from '../i18n'

import SearchInput from './SearchInput.vue'
import DownloadCounterPill from './DownloadCounterPill.vue'
import { openSettingsModal } from '../model/settingsModal'

const route = useRoute()
const themeMgr = useBinaryThemeManager({
  newLightAlias: 'downtify-light',
  newDarkAlias: 'downtify-dark',
})
const sm = useSearchManager()
const { t } = useI18n()
const { loading: healthRefreshLoading, refresh: refreshHealth } =
  useHealthRefresh()
const { loading: libraryRefreshLoading, failed: libraryRefreshFailed, refresh: refreshLibrary } =
  useLibraryRefresh()
</script>
