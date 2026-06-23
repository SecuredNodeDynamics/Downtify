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
          src="../assets/downtify.svg"
          class="h-7 w-7 drop-shadow-[0_0_8px_rgba(26,208,92,0.55)]"
          alt=""
        />
      </button>

      <h1 class="mobile-app-bar-title truncate">{{ pageTitle }}</h1>

      <div class="ml-auto flex shrink-0 items-center gap-1">
        <DownloadCounterPill compact />
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
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'

import router from '../router'
import { useHealthRefresh } from '../model/healthRefresh'
import { useI18n } from '../i18n'
import DownloadCounterPill from './DownloadCounterPill.vue'

const route = useRoute()
const { t } = useI18n()
const { loading: healthRefreshLoading, refresh: refreshHealth } = useHealthRefresh()

const showHealthRefresh = computed(() => route.name === 'Health')

const pageTitle = computed(() => {
  const key = route.meta?.mobileTitleKey
  if (key) return t(key)
  return 'Downtify'
})
</script>
