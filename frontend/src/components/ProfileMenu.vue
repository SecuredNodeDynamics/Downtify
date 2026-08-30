<template>
  <div v-if="user" ref="rootRef" class="relative">
    <button
      type="button"
      class="icon-btn max-w-[9rem] gap-1 px-2"
      :title="user.display_name || user.username"
      @click="open = !open"
    >
      <Icon icon="clarity:user-line" class="h-5 w-5 shrink-0" />
      <span class="hidden truncate text-xs font-semibold sm:inline">
        {{ user.display_name || user.username }}
      </span>
    </button>
    <div
      v-if="open"
      class="absolute right-0 z-40 mt-2 w-56 rounded-2xl border border-white/10 bg-base-100 p-2 shadow-xl"
    >
      <p
        class="px-2 py-1 text-[11px] uppercase tracking-wider text-base-content/40"
      >
        {{ t('auth.signedInAs') }}
      </p>
      <p class="truncate px-2 pb-2 text-sm font-semibold">
        {{ user.display_name || user.username }}
      </p>
      <button
        v-if="profiles.length > 1"
        type="button"
        class="flex w-full items-center gap-2 rounded-xl px-2 py-2 text-left text-sm hover:bg-white/5"
        @click="switchProfile"
      >
        <Icon icon="clarity:switch-line" class="h-4 w-4" />
        {{ t('auth.switchProfile') }}
      </button>
      <button
        type="button"
        class="flex w-full items-center gap-2 rounded-xl px-2 py-2 text-left text-sm hover:bg-white/5"
        @click="openAccounts"
      >
        <Icon icon="clarity:users-line" class="h-4 w-4" />
        {{ t('auth.accounts') }}
      </button>
      <button
        type="button"
        class="flex w-full items-center gap-2 rounded-xl px-2 py-2 text-left text-sm hover:bg-white/5"
        @click="signOut"
      >
        <Icon icon="clarity:logout-line" class="h-4 w-4" />
        {{ t('auth.signOut') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { Icon } from '@iconify/vue'

import API from '../model/api'
import { useAuthSession } from '../model/authSession'
import { openSettings } from '../model/settingsModal'
import { useI18n } from '../i18n'

const { t } = useI18n()
const { user, profiles } = useAuthSession()
const open = ref(false)
const rootRef = ref(null)

function onDocumentClick(event) {
  if (!rootRef.value?.contains(event.target)) open.value = false
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))

async function signOut() {
  open.value = false
  await API.logoutAccount()
}

async function switchProfile() {
  open.value = false
  await API.logoutAccount()
}

function openAccounts() {
  open.value = false
  openSettings('accounts')
}
</script>
