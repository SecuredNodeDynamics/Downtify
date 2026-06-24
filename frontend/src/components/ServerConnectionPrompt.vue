<template>
  <div
    v-if="needsServerConnection()"
    class="surface rounded-2xl border border-warning/30 bg-warning/10 p-4 sm:p-5"
  >
    <div class="flex gap-3">
      <Icon
        icon="clarity:warning-standard-line"
        class="h-5 w-5 shrink-0 text-warning"
      />
      <div class="min-w-0 space-y-3">
        <div>
          <p class="text-sm font-semibold">
            {{ t('settings.serverRequiredTitle') }}
          </p>
          <p class="mt-1 text-sm text-base-content/70">
            {{ t('settings.serverRequiredHint') }}
          </p>
        </div>
        <button
          type="button"
          class="btn btn-primary btn-sm h-10 rounded-full px-5"
          @click="goToServerSettings"
        >
          {{ t('settings.serverConnectionSection') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Icon } from '@iconify/vue'
import { useI18n } from '../i18n'
import { needsServerConnection } from '../model/serverConnection'
import { openSettings } from '../model/settingsModal'

const { t } = useI18n()

function goToServerSettings() {
  openSettings('api')
}
</script>
