<template>
  <div
    v-if="needsAuthGate"
    class="auth-gate"
    role="dialog"
    aria-modal="true"
    :aria-label="setupMode ? t('auth.setupTitle') : t('auth.loginTitle')"
  >
    <form class="auth-gate-card surface-strong" @submit.prevent="submit">
      <img :src="appIcon" alt="" class="auth-gate-logo" />
      <h1 class="auth-gate-title">
        {{ setupMode ? t('auth.setupTitle') : t('auth.loginTitle') }}
      </h1>
      <p class="auth-gate-copy">
        {{ setupMode ? t('auth.setupHint') : t('auth.loginHint') }}
      </p>

      <div v-if="!setupMode && profiles.length" class="auth-gate-profiles">
        <button
          v-for="profile in profiles"
          :key="profile.id"
          type="button"
          class="auth-gate-profile"
          :class="{ 'auth-gate-profile-active': username === profile.username }"
          @click="selectProfile(profile)"
        >
          <span class="auth-gate-profile-name">{{
            profile.display_name || profile.username
          }}</span>
          <span class="auth-gate-profile-meta">{{ profile.username }}</span>
        </button>
      </div>

      <label class="auth-gate-label">
        {{ t('auth.username') }}
        <input
          v-model.trim="username"
          class="input input-bordered w-full"
          autocomplete="username"
          required
        />
      </label>

      <label v-if="setupMode" class="auth-gate-label">
        {{ t('auth.displayName') }}
        <input
          v-model.trim="displayName"
          class="input input-bordered w-full"
          autocomplete="nickname"
        />
      </label>

      <label v-if="setupMode || showPasswordField" class="auth-gate-label">
        {{ t('auth.password') }}
        <input
          v-model="password"
          class="input input-bordered w-full"
          type="password"
          :autocomplete="setupMode ? 'new-password' : 'current-password'"
          :required="setupMode ? !pin : true"
        />
      </label>

      <label v-if="setupMode ? showSetupPin : showPinField" class="auth-gate-label">
        {{ t('auth.pin') }}
        <input
          v-model="pin"
          class="input input-bordered w-full"
          inputmode="numeric"
          autocomplete="off"
          maxlength="8"
          :required="setupMode ? !password : true"
        />
      </label>

      <button
        v-if="!setupMode && canSwitchMethod"
        type="button"
        class="auth-gate-switch"
        @click="toggleLoginMethod"
      >
        {{
          loginMethod === 'pin'
            ? t('auth.usePasswordInstead')
            : t('auth.usePinInstead')
        }}
      </button>

      <p v-if="errorText" class="auth-gate-error">{{ errorText }}</p>

      <button class="btn btn-primary w-full" type="submit" :disabled="busy">
        {{
          busy
            ? t('common.loading')
            : setupMode
              ? t('auth.createAdmin')
              : t('auth.signIn')
        }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import API from '../model/api'
import {
  canSwitchLoginMethod,
  loginRequestBody,
  preferredLoginMethod,
} from '../model/authLogin'
import { loadProfileBundle } from '../model/profileSync'
import { useAuthSession } from '../model/authSession'
import { usesEmbeddedServer } from '../model/serverConnection'
import { useI18n } from '../i18n'
import appIcon from '../assets/downtify-app-icon.png'

const { t } = useI18n()
const { needsAuthGate, status, profiles, errorMessage, loading } =
  useAuthSession()
const username = ref('')
const displayName = ref('')
const password = ref('')
const pin = ref('')
const loginMethod = ref('pin')
const busy = ref(false)
const localError = ref('')

const setupMode = computed(() => status.value.setup_required)
const deviceMode = computed(() => usesEmbeddedServer())
const selected = computed(() =>
  profiles.value.find(
    (profile) => profile.username.toLowerCase() === username.value.toLowerCase()
  )
)
const showSetupPin = computed(() => deviceMode.value)
const canSwitchMethod = computed(
  () => !setupMode.value && canSwitchLoginMethod(selected.value)
)
const showPinField = computed(
  () => !setupMode.value && loginMethod.value === 'pin'
)
const showPasswordField = computed(
  () => !setupMode.value && loginMethod.value === 'password'
)
const errorText = computed(() => localError.value || errorMessage.value || '')

watch(
  profiles,
  (list) => {
    if (username.value || !list?.length) return
    selectProfile(list[0])
  },
  { immediate: true }
)

watch(selected, (profile) => {
  if (setupMode.value) return
  loginMethod.value = preferredLoginMethod(profile)
})

function selectProfile(profile) {
  username.value = profile.username
  displayName.value = profile.display_name || profile.username
  password.value = ''
  pin.value = ''
  loginMethod.value = preferredLoginMethod(profile)
  localError.value = ''
}

function toggleLoginMethod() {
  loginMethod.value = loginMethod.value === 'pin' ? 'password' : 'pin'
  password.value = ''
  pin.value = ''
  localError.value = ''
}

async function submit() {
  localError.value = ''
  busy.value = true
  loading.value = true
  try {
    const cached = loadProfileBundle({ username: username.value })
    const payload = loginRequestBody({
      username: username.value,
      displayName: displayName.value,
      password: password.value,
      pin: pin.value,
      method: loginMethod.value,
      setup: setupMode.value,
      profileKey: cached?.profile_key || '',
    })
    if (setupMode.value) {
      await API.setupAccount(payload)
    } else {
      await API.loginAccount(payload)
    }
    password.value = ''
    pin.value = ''
  } catch (err) {
    if (setupMode.value && err?.response?.status === 409) {
      await API.fetchAuthStatus()
      localError.value = ''
      return
    }
    localError.value =
      err?.response?.data?.detail || err?.message || t('auth.failed')
  } finally {
    busy.value = false
    loading.value = false
  }
}
</script>

<style scoped>
.auth-gate {
  @apply fixed inset-0 z-[190] flex items-center justify-center bg-base-100/80 p-4 backdrop-blur-[4px];
  padding-top: var(--app-safe-top);
  padding-bottom: var(--app-safe-bottom);
}
.auth-gate-card {
  @apply flex w-full max-w-md flex-col gap-3 rounded-3xl border border-white/10 p-6 shadow-glow;
}
.auth-gate-logo {
  @apply mx-auto h-14 w-14 rounded-2xl object-cover;
}
.auth-gate-title {
  @apply text-center text-xl font-bold;
}
.auth-gate-copy {
  @apply text-center text-sm text-base-content/60;
}
.auth-gate-label {
  @apply flex flex-col gap-1 text-xs font-semibold uppercase tracking-wider text-base-content/50;
}
.auth-gate-profiles {
  @apply grid gap-2;
}
.auth-gate-profile {
  @apply flex flex-col items-start rounded-xl border border-white/10 px-3 py-2 text-left transition-colors;
}
.auth-gate-profile-active {
  @apply border-primary/50 bg-primary/10;
}
.auth-gate-profile-name {
  @apply text-sm font-semibold normal-case;
}
.auth-gate-profile-meta {
  @apply text-[11px] font-normal normal-case text-base-content/50;
}
.auth-gate-error {
  @apply text-sm text-error;
}
.auth-gate-switch {
  @apply btn btn-ghost btn-sm h-auto min-h-0 justify-center px-0 py-1 text-xs font-semibold normal-case tracking-normal text-primary;
}
</style>
