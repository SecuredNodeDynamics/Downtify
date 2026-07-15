<template>
  <header class="mobile-app-bar lg:hidden">
    <div class="mobile-app-bar-inner safe-top">
      <button
        type="button"
        class="mobile-app-bar-logo"
        :title="t('nav.home')"
        @click="router.push({ name: 'Home' })"
      >
        <img
          :src="appIcon"
          class="h-7 w-7 rounded-lg object-cover drop-shadow-[0_0_8px_rgba(26,208,92,0.55)]"
          alt=""
        />
      </button>

      <h1 class="mobile-app-bar-title truncate">{{ pageTitle }}</h1>

      <div class="ml-auto flex shrink-0 items-center gap-1">
        <HeaderUpdateNotice compact />
        <DownloadCounterPill compact />
        <button
          v-if="routeAction && routeAction.routeName === route.name"
          type="button"
          class="mobile-app-bar-icon shrink-0"
          :title="routeAction.title || routeAction.label || ''"
          @click="routeAction.onClick?.()"
        >
          <Icon
            :icon="routeAction.icon || 'clarity:menu-line'"
            class="h-5 w-5"
          />
        </button>
        <button
          v-if="showLibraryRefresh"
          type="button"
          class="mobile-app-bar-icon shrink-0"
          :class="{ 'mobile-app-bar-icon-error': libraryRefreshFailed }"
          :title="t('common.refresh')"
          :disabled="libraryRefreshLoading"
          @click.stop.prevent="refreshLibraryInPlace"
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
          v-if="showHealthRefresh"
          type="button"
          class="mobile-app-bar-icon shrink-0"
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
          v-if="showDownloadRefresh"
          type="button"
          class="mobile-app-bar-icon shrink-0"
          :title="t('common.refresh')"
          :disabled="downloadRefreshLoading"
          @click="refreshDownload()"
        >
          <Icon
            icon="clarity:refresh-line"
            class="h-5 w-5 transition-colors"
            :class="downloadRefreshLoading ? 'animate-spin text-primary' : ''"
          />
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'

import router from '../router'
import { useDownloadRefresh } from '../model/downloadRefresh'
import { useHealthRefresh } from '../model/healthRefresh'
import { useLibraryRefresh } from '../model/libraryRefresh'
import { useI18n } from '../i18n'
import DownloadCounterPill from './DownloadCounterPill.vue'
import HeaderUpdateNotice from './HeaderUpdateNotice.vue'
import appIcon from '../assets/downtify-app-icon.png'

const route = useRoute()
const { t } = useI18n()
const { loading: healthRefreshLoading, refresh: refreshHealth } =
  useHealthRefresh()
const {
  loading: libraryRefreshLoading,
  failed: libraryRefreshFailed,
  refresh: refreshLibrary,
} = useLibraryRefresh()
const {
  loading: downloadRefreshLoading,
  visible: downloadRefreshVisible,
  refresh: refreshDownload,
} = useDownloadRefresh()
const routeAction = ref(null)

const showHealthRefresh = computed(() => route.name === 'Health')
const showLibraryRefresh = computed(() => route.name === 'List')
const showDownloadRefresh = computed(
  () =>
    route.name === 'Download' &&
    downloadRefreshVisible.value &&
    !(routeAction.value && routeAction.value.routeName === route.name)
)

const pageTitle = computed(() => {
  const key = route.meta?.mobileTitleKey
  if (key) return t(key)
  return 'Downtify'
})

function handleRouteAction(event) {
  routeAction.value = event?.detail || null
}

function clearRouteAction(event) {
  const routeName = event?.detail?.routeName
  if (!routeName || routeAction.value?.routeName === routeName) {
    routeAction.value = null
  }
}

async function refreshLibraryInPlace() {
  if (route.name !== 'List') return
  const originalPath = route.fullPath
  await refreshLibrary()
  if (router.currentRoute.value.name === 'Home') {
    await router.replace(originalPath || { name: 'List' })
  }
}

onMounted(() => {
  window.addEventListener('downtify:mobile-route-action', handleRouteAction)
  window.addEventListener(
    'downtify:clear-mobile-route-action',
    clearRouteAction
  )
})

onBeforeUnmount(() => {
  window.removeEventListener('downtify:mobile-route-action', handleRouteAction)
  window.removeEventListener(
    'downtify:clear-mobile-route-action',
    clearRouteAction
  )
})
</script>
