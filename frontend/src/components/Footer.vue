<template>
  <footer class="mt-auto px-6 py-6 text-center text-sm text-base-content/60">
    <a
      class="font-semibold text-primary hover:underline"
      href="https://github.com/SecuredNodeDynamics/Downtify"
      target="_blank"
      rel="noopener"
      >Downtify</a
    >
    <span class="mx-2 opacity-50">·</span>
    <span>{{ t('footer.tagline') }}</span>
    <template v-if="updateAvailable">
      <span class="mx-2 opacity-50">·</span>
      <button
        type="button"
        class="font-semibold text-success hover:underline"
        @click="openUpdateSettings"
      >
        {{ t('footer.updateAvailable') }}
      </button>
    </template>
  </footer>
</template>

<script setup>
import { useI18n } from '../i18n'
import { useAppUpdateNotice } from '../model/appUpdateNotice'

const { t } = useI18n()
const { updateAvailable, openUpdateSettings } = useAppUpdateNotice()
</script>
