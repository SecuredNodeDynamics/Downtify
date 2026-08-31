<template>
  <div class="space-y-3">
    <div class="surface rounded-xl px-3 py-2.5 text-sm">
      <span class="text-base-content/50">
        {{ t('settings.serverUrlCurrent') }}:
      </span>
      <span class="ml-1 font-medium text-base-content">
        {{
          usesCustomServer
            ? activeServerDisplay
            : t('settings.serverUrlDefault')
        }}
      </span>
      <span
        v-if="usesCustomServer"
        class="ml-1.5 text-[11px] text-base-content/45"
      >
        ({{
          activeRoute === 'public'
            ? t('settings.serverRoutePublic')
            : t('settings.serverRoutePrivate')
        }})
      </span>
    </div>

    <div class="grid grid-cols-2 gap-2">
      <button
        type="button"
        class="rounded-xl border px-3 py-2 text-sm transition-colors text-left"
        :class="routeButtonClass('private')"
        :disabled="serverTestLoading"
        @click="selectedRoute = 'private'"
      >
        {{ t('settings.serverRoutePrivate') }}
      </button>
      <button
        type="button"
        class="rounded-xl border px-3 py-2 text-sm transition-colors text-left"
        :class="routeButtonClass('public')"
        :disabled="serverTestLoading"
        @click="selectedRoute = 'public'"
      >
        {{ t('settings.serverRoutePublic') }}
      </button>
    </div>
    <p class="text-[11px] text-base-content/40">
      {{ t('settings.serverRouteHint') }}
    </p>

    <div>
      <label class="block text-xs text-base-content/50 mb-1.5">
        {{ t('settings.serverUrlPrivate') }}
      </label>
      <input
        v-model="privateUrlInput"
        type="url"
        inputmode="url"
        autocapitalize="off"
        autocorrect="off"
        spellcheck="false"
        class="input-modern h-10 w-full text-sm"
        :placeholder="t('settings.serverUrlPrivatePlaceholder')"
      />
    </div>
    <div>
      <label class="block text-xs text-base-content/50 mb-1.5">
        {{ t('settings.serverUrlPublic') }}
      </label>
      <input
        v-model="publicUrlInput"
        type="url"
        inputmode="url"
        autocapitalize="off"
        autocorrect="off"
        spellcheck="false"
        class="input-modern h-10 w-full text-sm"
        :placeholder="t('settings.serverUrlPublicPlaceholder')"
      />
      <p class="text-[11px] text-base-content/40 mt-1.5">
        {{ t('settings.serverSaveHint') }}
      </p>
    </div>

    <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
      <button
        v-if="canConnectDevice"
        type="button"
        class="btn btn-primary btn-sm h-10 w-full rounded-full px-4 sm:w-auto"
        :disabled="connectedToThisDevice || serverTestLoading"
        @click="connectToThisDevice"
      >
        {{ t('settings.serverConnectDevice') }}
      </button>
      <button
        type="button"
        class="btn btn-sm h-10 w-full rounded-full px-4 sm:w-auto"
        :class="
          canConnectDevice
            ? 'border border-white/10 bg-base-100/85 text-base-content hover:bg-base-100'
            : 'btn-primary'
        "
        :disabled="serverTestLoading || !activeInput.trim()"
        @click="testActiveConnection"
      >
        <span
          v-if="serverTestLoading"
          class="loading loading-spinner loading-xs mr-2"
        />
        {{
          serverTestLoading
            ? t('settings.serverTesting')
            : t('settings.serverTest')
        }}
      </button>
      <button
        type="button"
        class="btn btn-sm h-10 w-full rounded-full border border-white/10 bg-base-100/85 px-4 text-base-content hover:bg-base-100 sm:w-auto"
        :disabled="!canSaveActiveUrl || serverTestLoading"
        @click="saveActiveConnection"
      >
        {{ t('settings.serverSave') }}
      </button>
      <button
        v-if="usesCustomServer && !connectedToThisDevice"
        type="button"
        class="btn btn-sm h-10 w-full rounded-full border border-white/10 bg-base-100/85 px-4 text-base-content hover:bg-base-100 sm:w-auto"
        @click="resetServerConnection"
      >
        {{ t('settings.serverClear') }}
      </button>
    </div>
    <p
      v-if="serverTestMessage"
      class="text-[11px]"
      :class="serverTestError ? 'text-error' : 'text-primary'"
    >
      {{ serverTestMessage }}
    </p>
  </div>
</template>

<script setup>
import axios from 'axios'
import { computed, ref } from 'vue'
import { useI18n } from '../i18n'
import API from '../model/api'
import {
  buildApiBaseUrl,
  canConnectToCurrentPage,
  canSaveServerUrlInput,
  configuredServerBaseUrl,
  formatServerDisplay,
  getActiveServerRoute,
  getCurrentPageServerUrl,
  getServerConfig,
  getStoredPrivateServerUrl,
  getStoredPublicServerUrl,
  isCapacitorNative,
  isConnectedToCurrentPage,
  parseServerUrl,
  SERVER_ROUTE_PRIVATE,
  SERVER_ROUTE_PUBLIC,
  setActiveServerRoute,
  setConnectionMode,
  setStoredPrivateServerUrl,
  setStoredPublicServerUrl,
  setStoredServerUrl,
  usesCustomServerUrl,
} from '../model/serverConnection'

const { t } = useI18n()

const privateUrlInput = ref(getStoredPrivateServerUrl())
const publicUrlInput = ref(getStoredPublicServerUrl())
const selectedRoute = ref(getActiveServerRoute())
const serverTestLoading = ref(false)
const serverTestMessage = ref('')
const serverTestError = ref(false)

const usesCustomServer = computed(() => usesCustomServerUrl())
const activeRoute = computed(() => getActiveServerRoute())
const activeServerDisplay = computed(() =>
  formatServerDisplay(getServerConfig())
)
const canConnectDevice = computed(() => canConnectToCurrentPage())
const connectedToThisDevice = computed(() => isConnectedToCurrentPage())
const activeInput = computed(() =>
  selectedRoute.value === SERVER_ROUTE_PUBLIC
    ? publicUrlInput.value
    : privateUrlInput.value
)
function isUsingUrl(raw) {
  const parsed = parseServerUrl(raw)
  if (!parsed || !usesCustomServerUrl()) return false
  return buildApiBaseUrl(parsed) === configuredServerBaseUrl()
}

const canSaveActiveUrl = computed(() => {
  if (!parseServerUrl(activeInput.value)) return false
  if (isUsingUrl(activeInput.value)) return false
  return canSaveServerUrlInput(activeInput.value) || isCapacitorNative()
})

function routeButtonClass(route) {
  const selected = selectedRoute.value === route
  const connected = usesCustomServer.value && activeRoute.value === route
  if (connected) {
    return 'border-primary/50 bg-primary/10 text-primary'
  }
  if (selected) {
    return 'border-white/25 bg-white/5 text-base-content'
  }
  return 'border-white/10 hover:border-white/20 hover:bg-white/5'
}

async function snapshotThenReload(mutate) {
  await API.snapshotProfile().catch(() => {})
  mutate?.()
  if (isCapacitorNative()) {
    API.reconnectBackend()
  }
  window.location.reload()
}

function persistValidSlots() {
  const priv = parseServerUrl(privateUrlInput.value)
  const pub = parseServerUrl(publicUrlInput.value)
  if (priv) setStoredPrivateServerUrl(buildApiBaseUrl(priv))
  if (pub) setStoredPublicServerUrl(buildApiBaseUrl(pub))
}

function persistSlot(route, raw) {
  persistValidSlots()
  const parsed = parseServerUrl(raw)
  const canonical = parsed ? buildApiBaseUrl(parsed) : String(raw || '').trim()
  if (route === SERVER_ROUTE_PUBLIC) {
    setStoredPublicServerUrl(canonical)
  } else {
    setStoredPrivateServerUrl(canonical)
  }
  setActiveServerRoute(route)
  setConnectionMode('server')
}

async function testActiveConnection() {
  serverTestMessage.value = ''
  serverTestError.value = false
  const parsed = parseServerUrl(activeInput.value)
  if (!parsed) {
    serverTestError.value = true
    serverTestMessage.value = t('settings.serverInvalidUrl')
    return
  }
  serverTestLoading.value = true
  try {
    const client = axios.create({
      baseURL: buildApiBaseUrl(parsed),
      timeout: 15000,
    })
    const [healthRes, versionRes] = await Promise.all([
      client.get('/api/health'),
      client.get('/api/version'),
    ])
    const version = String(versionRes.data || '').trim()
    if (!healthRes.data || healthRes.status !== 200) {
      throw new Error(t('settings.serverTestFailed'))
    }
    serverTestMessage.value = t('settings.serverTestSuccess', {
      version: version || '?',
    })
  } catch (err) {
    serverTestError.value = true
    const detail = err?.response?.data?.detail || err?.message
    serverTestMessage.value = detail
      ? `${t('settings.serverTestFailed')}: ${detail}`
      : t('settings.serverTestFailed')
  } finally {
    serverTestLoading.value = false
  }
}

function connectToThisDevice() {
  const current = getCurrentPageServerUrl()
  if (!current) return
  privateUrlInput.value = current
  selectedRoute.value = SERVER_ROUTE_PRIVATE
  if (isConnectedToCurrentPage()) return
  void snapshotThenReload(() => {
    setStoredServerUrl(current)
    setConnectionMode('server')
  })
}

function saveActiveConnection() {
  const parsed = parseServerUrl(activeInput.value)
  if (!parsed) {
    serverTestError.value = true
    serverTestMessage.value = t('settings.serverInvalidUrl')
    return
  }
  void snapshotThenReload(() =>
    persistSlot(selectedRoute.value, activeInput.value)
  )
}

function resetServerConnection() {
  void snapshotThenReload(() => {
    setStoredServerUrl('')
  })
}
</script>
