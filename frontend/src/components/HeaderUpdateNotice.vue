<template>
  <button
    v-if="updateAvailable"
    type="button"
    class="header-update-notice"
    :class="
      compact ? 'mobile-app-bar-icon header-update-notice-mobile' : 'icon-btn'
    "
    :title="t('nav.updateAvailable')"
    :aria-label="t('nav.updateAvailable')"
    @click="openUpdateSettings"
  >
    <Icon icon="clarity:download-cloud-line" class="h-5 w-5" />
  </button>
</template>

<script setup>
import { Icon } from '@iconify/vue'

import { useI18n } from '../i18n'
import { useAppUpdateNotice } from '../model/appUpdateNotice'

defineProps({
  compact: { type: Boolean, default: false },
})

const { t } = useI18n()
const { updateAvailable, openUpdateSettings } = useAppUpdateNotice()
</script>
