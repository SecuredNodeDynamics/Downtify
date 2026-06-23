<template>
  <input id="mobile-more-sheet" type="checkbox" class="modal-toggle" />
  <div class="modal modal-bottom lg:hidden">
    <div class="modal-box mobile-more-sheet safe-bottom">
      <div class="mobile-more-sheet-handle" aria-hidden="true" />

      <h2 class="mobile-more-sheet-title">{{ t('nav.more') }}</h2>

      <div class="mobile-more-list">
        <button
          v-for="item in menuItems"
          :key="item.name"
          type="button"
          class="mobile-more-item"
          :class="{ 'mobile-more-item-active': route.name === item.name }"
          @click="go(item.name)"
        >
          <Icon :icon="item.icon" class="h-5 w-5 shrink-0" />
          <span class="flex-1 text-left">{{ t(item.labelKey) }}</span>
          <Icon icon="clarity:angle-line" class="h-4 w-4 -rotate-90 opacity-40" />
        </button>

        <button
          type="button"
          class="mobile-more-item"
          @click="toggleTheme"
        >
          <Icon
            :icon="
              themeMgr.currentTheme.value === 'dark'
                ? 'clarity:sun-line'
                : 'clarity:moon-line'
            "
            class="h-5 w-5 shrink-0"
          />
          <span class="flex-1 text-left">
            {{
              themeMgr.currentTheme.value === 'dark'
                ? t('nav.switchToLight')
                : t('nav.switchToDark')
            }}
          </span>
        </button>

        <label
          for="settings-modal"
          class="mobile-more-item cursor-pointer"
          @click="closeSheet"
        >
          <Icon icon="clarity:cog-line" class="h-5 w-5 shrink-0" />
          <span class="flex-1 text-left">{{ t('nav.settings') }}</span>
        </label>
      </div>

      <label for="mobile-more-sheet" class="mobile-more-cancel">
        {{ t('common.cancel') }}
      </label>
    </div>
    <label for="mobile-more-sheet" class="modal-backdrop" />
  </div>
</template>

<script setup>
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'

import router from '../router'
import { useBinaryThemeManager } from '../model/theme'
import { useI18n } from '../i18n'

const route = useRoute()
const { t } = useI18n()
const themeMgr = useBinaryThemeManager({
  newLightAlias: 'downtify-light',
  newDarkAlias: 'downtify-dark',
})

const menuItems = [
  { name: 'Monitor', labelKey: 'nav.monitor', icon: 'clarity:eye-line' },
  { name: 'Health', labelKey: 'nav.health', icon: 'clarity:info-standard-line' },
  { name: 'Metadata', labelKey: 'nav.metadata', icon: 'clarity:tag-line' },
]

function closeSheet() {
  const sheet = document.getElementById('mobile-more-sheet')
  if (sheet) sheet.checked = false
}

function go(name) {
  closeSheet()
  router.push({ name })
}

function toggleTheme() {
  themeMgr.setTheme(themeMgr.currentTheme.value === 'dark' ? 'light' : 'dark')
  closeSheet()
}
</script>
