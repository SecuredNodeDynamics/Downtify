<template>
  <StarField v-show="!starFieldPaused" :paused="starFieldPaused" />
  <AppLoadingOverlay />
  <AuthGate />
  <div
    class="app-shell flex min-h-dvh flex-col overflow-x-hidden text-base-content lg:min-h-dvh lg:overflow-visible"
  >
    <MobileAppBar />
    <main
      class="mobile-main flex-1 overflow-x-hidden"
      :class="{ 'has-mini-player': showMiniPlayer }"
    >
      <template v-if="isNativeApp">
        <HomePage v-if="mountedNativeTabs.Home" v-show="nativeTab === 'Home'" />
        <ListPage v-if="mountedNativeTabs.List" v-show="nativeTab === 'List'" />
        <PlayerPage
          v-if="mountedNativeTabs.Player"
          v-show="nativeTab === 'Player'"
        />
        <SearchPage
          v-if="mountedNativeTabs.Search"
          v-show="nativeTab === 'Search'"
        />
        <DownloadPage
          v-if="mountedNativeTabs.Download"
          v-show="nativeTab === 'Download'"
        />
        <SettingsPage
          v-if="mountedNativeTabs.Settings"
          v-show="nativeTab === 'Settings'"
        />
        <MonitorPage
          v-if="mountedNativeTabs.Monitor"
          v-show="nativeTab === 'Monitor'"
        />
        <HealthPage
          v-if="mountedNativeTabs.Health"
          v-show="nativeTab === 'Health'"
        />
        <MetadataPage
          v-if="mountedNativeTabs.Metadata"
          v-show="nativeTab === 'Metadata'"
        />
        <ArtistPage
          v-if="mountedNativeTabs.Artist"
          v-show="nativeTab === 'Artist'"
        />
      </template>
      <router-view v-if="!isNativeTabRoute" v-slot="{ Component, route }">
        <keep-alive :include="keepAliveViews">
          <component :is="Component" :key="route.name" />
        </keep-alive>
      </router-view>
    </main>
    <Footer class="hidden lg:block" />
    <MiniPlayer />
    <BottomNav />
    <MobileMoreSheet />
    <MobileSearchSheet />
  </div>
</template>

<script setup>
import {
  computed,
  defineAsyncComponent,
  nextTick,
  onBeforeMount,
  onMounted,
  reactive,
  watch,
} from 'vue'
import { useRoute } from 'vue-router'

import AuthGate from './components/AuthGate.vue'
import AppLoadingOverlay from './components/AppLoadingOverlay.vue'
import BottomNav from './components/BottomNav.vue'
import Footer from './components/Footer.vue'
import MiniPlayer from './components/MiniPlayer.vue'
import MobileAppBar from './components/MobileAppBar.vue'
import MobileMoreSheet from './components/MobileMoreSheet.vue'
import MobileSearchSheet from './components/MobileSearchSheet.vue'
import StarField from './components/StarField.vue'
import HomePage from './views/Front.vue'
import router, { preloadRouteComponents } from './router'
import API from './model/api'
import { bootstrapAppUpdateNotice } from './model/appUpdateNotice'
import {
  bootstrapEmbeddedServer,
  EMBEDDED_SERVER_READY_EVENT,
} from './model/embeddedServer'
import { setCoverWarmPaused } from './model/imageLoader'
import { isCapacitorNative, usesEmbeddedServer } from './model/serverConnection'
import { authStatus, ready as authReady } from './model/authSession'
import { usePlayer } from './model/player'
import { useBinaryThemeManager } from './model/theme'

const ListPage = defineAsyncComponent(() => import('./views/Downloads.vue'))
const PlayerPage = defineAsyncComponent(() => import('./views/Player.vue'))
const SearchPage = defineAsyncComponent(() => import('./views/Search.vue'))
const DownloadPage = defineAsyncComponent(() => import('./views/Download.vue'))
const SettingsPage = defineAsyncComponent(() => import('./views/Settings.vue'))
const MonitorPage = defineAsyncComponent(() => import('./views/Monitor.vue'))
const HealthPage = defineAsyncComponent(() => import('./views/Health.vue'))
const MetadataPage = defineAsyncComponent(() => import('./views/Metadata.vue'))
const ArtistPage = defineAsyncComponent(() => import('./views/Artist.vue'))

const route = useRoute()
const player = usePlayer()
const isNativeApp = isCapacitorNative()
const nativeTabNames = {
  Home: 'Home',
  List: 'List',
  Player: 'Player',
  Search: 'Search',
  SearchLegacy: 'Search',
  Download: 'Download',
  Settings: 'Settings',
  Monitor: 'Monitor',
  Health: 'Health',
  Metadata: 'Metadata',
  Artist: 'Artist',
}
const nativeTab = computed(() => nativeTabNames[route.name] || null)
const isNativeTabRoute = computed(() => isNativeApp && Boolean(nativeTab.value))
const mountedNativeTabs = reactive({
  Home: false,
  List: false,
  Player: false,
  Search: false,
  Download: false,
  Settings: false,
  Monitor: false,
  Health: false,
  Metadata: false,
  Artist: false,
})
const starFieldPaused = computed(
  () => isNativeApp && nativeTab.value !== 'Home'
)
const showMiniPlayer = computed(
  () => Boolean(player.currentTrack.value) && route.name !== 'Player'
)
const keepAliveViews = [
  'Home',
  'Player',
  'List',
  'Search',
  'Settings',
  'Download',
  'Artist',
  'Monitor',
  'Health',
  'Metadata',
]

watch(
  nativeTab,
  (tab) => {
    if (tab && tab in mountedNativeTabs) mountedNativeTabs[tab] = true
  },
  { immediate: true }
)

watch(
  () => route.name,
  () => {
    if (!isNativeApp) return
    setCoverWarmPaused(true)
    window.setTimeout(() => setCoverWarmPaused(false), 450)
  }
)

const themeMgr = useBinaryThemeManager()
onBeforeMount(() => {
  themeMgr.setLightAlias('downtify-light')
  themeMgr.setDarkAlias('downtify-dark')
})

watch(
  () => [
    authReady.value,
    authStatus.value.auth_required,
    authStatus.value.user,
    route.name,
  ],
  () => {
    if (!route.meta?.requiresAdmin) return
    if (!authStatus.value.auth_required) return
    if (authStatus.value.user?.is_admin) return
    if (route.name === 'Home') return
    router.replace({ name: 'Home' })
  }
)

onMounted(async () => {
  void bootstrapEmbeddedServer().then(() => {
    if (usesEmbeddedServer()) {
      window.dispatchEvent(new CustomEvent(EMBEDDED_SERVER_READY_EVENT))
    }
    void startMountedBackendSession()
  })
  if (!usesEmbeddedServer()) {
    void startMountedBackendSession()
  }
  window.setTimeout(preloadRouteComponents, 200)

  bootstrapAppUpdateNotice()

  const capacitor = window.Capacitor
  if (!capacitor?.isNativePlatform?.()) return
  try {
    const [{ App }, { resolveNativeInstalledVersion }] = await Promise.all([
      import('@capacitor/app'),
      import('./model/appVersion'),
    ])
    await resolveNativeInstalledVersion()
    await App.addListener('backButton', () => {
      for (const id of ['mobile-more-sheet', 'mobile-search-sheet']) {
        const sheet = document.getElementById(id)
        if (sheet?.checked) {
          sheet.checked = false
          return
        }
      }
      if (
        window.history.length > 1 &&
        router.currentRoute.value.name !== 'Home'
      ) {
        router.back()
        return
      }
      App.exitApp()
    })
  } catch {
    // Capacitor app plugin unavailable in web builds.
  }
})

async function startMountedBackendSession() {
  await nextTick()
  await new Promise((resolve) =>
    window.requestAnimationFrame(() => window.requestAnimationFrame(resolve))
  )
  await API.startBackendSession()
}
</script>
