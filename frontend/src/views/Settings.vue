<template>
  <div class="min-h-0 overflow-x-hidden pb-24 lg:pb-8">
    <Navbar />

    <div class="mx-auto max-w-3xl w-full min-w-0 px-4 py-4 sm:py-8 sm:px-6">
      <ServerConnectionPrompt class="mb-4" />

      <div class="mb-4 mobile-page-header hidden lg:block">
        <h1 class="text-2xl font-bold tracking-tight">
          {{ t('settings.title') }}
        </h1>
        <p class="mt-1 text-sm text-base-content/60">
          {{ t('settings.subtitle') }}
        </p>
      </div>

      <SettingsPanel />
    </div>
  </div>
</template>

<script setup>
import Navbar from '../components/Navbar.vue'
import ServerConnectionPrompt from '../components/ServerConnectionPrompt.vue'
import SettingsPanel from '../components/SettingsPanel.vue'
import { useI18n } from '../i18n'

defineOptions({ name: 'Settings' })

const { t } = useI18n()
</script>
