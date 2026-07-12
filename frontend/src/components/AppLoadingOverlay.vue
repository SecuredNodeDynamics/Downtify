<template>
  <Transition name="app-loading-fade">
    <div
      v-if="visible"
      class="app-loading-overlay"
      role="status"
      aria-live="polite"
      :aria-label="t('common.loading')"
    >
      <div class="app-loading-card">
        <img
          :src="appIcon"
          alt=""
          class="app-loading-logo"
          aria-hidden="true"
        />
        <Icon icon="clarity:refresh-line" class="app-loading-spinner" />
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { Icon } from '@iconify/vue'

import { useAppLoading } from '../model/appLoading'
import { useI18n } from '../i18n'
import appIcon from '../assets/downtify-app-icon.png'

const { visible } = useAppLoading()
const { t } = useI18n()
</script>
