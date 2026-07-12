<template>
  <header class="absolute top-0 inset-x-0 z-30 hidden lg:block">
    <div
      class="mx-auto flex h-16 w-full max-w-6xl items-center gap-3 px-4 sm:px-6"
    >
      <div class="flex items-center gap-2">
        <img
          :src="appIcon"
          class="h-8 w-8 rounded-xl object-cover drop-shadow-[0_0_8px_rgba(26,208,92,0.55)]"
          alt=""
        />
        <span class="text-lg font-bold tracking-tight">Downtify</span>
      </div>
      <div class="ml-auto flex items-center gap-2 sm:gap-3">
        <DownloadCounterPill />

        <div class="flex items-center gap-1 sm:gap-2">
          <button
            class="icon-btn"
            @click="router.push({ name: 'List' })"
            :title="t('nav.library')"
          >
            <Icon icon="clarity:library-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            @click="router.push({ name: 'Player' })"
            :title="t('nav.player')"
          >
            <Icon icon="clarity:headphones-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            @click="router.push({ name: 'Monitor' })"
            :title="t('nav.monitor')"
          >
            <Icon icon="clarity:eye-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            @click="router.push({ name: 'Health' })"
            :title="t('nav.health')"
          >
            <Icon icon="clarity:info-standard-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            @click="router.push({ name: 'Metadata' })"
            :title="t('nav.metadata')"
          >
            <Icon icon="clarity:tag-line" class="h-5 w-5" />
          </button>

          <button
            class="icon-btn"
            @click="router.push({ name: 'Download' })"
            :title="t('nav.queue')"
          >
            <Icon icon="clarity:download-line" class="h-5 w-5" />
          </button>

          <HeaderUpdateNotice />

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
import router from '../router'
import { useBinaryThemeManager } from '../model/theme'
import { useI18n } from '../i18n'
import { openSettingsModal } from '../model/settingsModal'
import appIcon from '../assets/downtify-app-icon.png'
import DownloadCounterPill from './DownloadCounterPill.vue'
import HeaderUpdateNotice from './HeaderUpdateNotice.vue'

const themeMgr = useBinaryThemeManager({
  newLightAlias: 'downtify-light',
  newDarkAlias: 'downtify-dark',
})
const { t } = useI18n()
</script>
