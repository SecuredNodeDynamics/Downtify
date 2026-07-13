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
        <Icon
          v-if="!engineFailed"
          icon="clarity:refresh-line"
          class="app-loading-spinner"
        />
        <Icon
          v-else
          icon="clarity:exclamation-circle-line"
          class="app-loading-error-icon"
        />
        <p v-if="engineStarting || engineFailed" class="app-loading-title">
          {{
            engineFailed ? t('engine.failedTitle') : t('engine.startingTitle')
          }}
        </p>
        <p v-if="engineStarting || engineFailed" class="app-loading-subtitle">
          {{ engineFailed ? t('engine.failedHint') : t('engine.startingHint') }}
        </p>
        <button
          v-if="engineFailed"
          type="button"
          class="app-loading-retry"
          @click="retryEmbeddedServerBootstrap"
        >
          <Icon icon="clarity:refresh-line" class="h-4 w-4" />
          {{ t('engine.retry') }}
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

import { useAppLoading } from '../model/appLoading'
import {
  retryEmbeddedServerBootstrap,
  useEmbeddedServerStatus,
} from '../model/embeddedServer'
import { useI18n } from '../i18n'
import appIcon from '../assets/downtify-app-icon.png'

const { visible: appLoadingVisible } = useAppLoading()
const { starting: engineStarting, failed: engineFailed } =
  useEmbeddedServerStatus()
const { t } = useI18n()
const visible = computed(
  () => appLoadingVisible.value || engineStarting.value || engineFailed.value
)
</script>
