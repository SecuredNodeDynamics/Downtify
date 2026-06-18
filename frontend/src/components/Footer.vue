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
import { onMounted, ref } from 'vue'
import { useI18n } from '../i18n'
import API from '../model/api'

const { t } = useI18n()
const updateAvailable = ref(false)

onMounted(async () => {
  try {
    const response = await API.check_for_update()
    updateAvailable.value = Boolean(response.data?.update_available)
  } catch {
    updateAvailable.value = false
  }
})

function openUpdateSettings() {
  window.dispatchEvent(
    new CustomEvent('downtify:open-settings', { detail: { tab: 'help' } })
  )
  const modal = document.getElementById('settings-modal')
  if (modal) modal.checked = true
}
</script>
