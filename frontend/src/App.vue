<template>
  <StarField v-if="!isNativeApp" />
  <AppLoadingOverlay />
  <div
    class="app-shell flex min-h-dvh flex-col overflow-x-hidden text-base-content lg:min-h-dvh lg:overflow-visible"
  >
    <MobileAppBar />
    <main class="mobile-main flex-1 overflow-x-hidden">
      <router-view v-slot="{ Component, route }">
        <transition :name="routeTransitionName(route)">
          <keep-alive :include="keepAliveViews">
            <component :is="Component" :key="route.name" />
          </keep-alive>
        </transition>
      </router-view>
    </main>
    <Footer class="hidden lg:block" />
    <BottomNav />
    <MobileMoreSheet />
    <MobileSearchSheet />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeMount, onMounted } from 'vue'

import AppLoadingOverlay from './components/AppLoadingOverlay.vue'
import BottomNav from './components/BottomNav.vue'
import Footer from './components/Footer.vue'
import MobileAppBar from './components/MobileAppBar.vue'
import MobileMoreSheet from './components/MobileMoreSheet.vue'
import MobileSearchSheet from './components/MobileSearchSheet.vue'
import StarField from './components/StarField.vue'
import router, { preloadRouteComponents } from './router'
import API from './model/api'
import { beginAppLoading, endAppLoading } from './model/appLoading'
import { bootstrapAppUpdateNotice } from './model/appUpdateNotice'
import {
  bootstrapEmbeddedServer,
  EMBEDDED_SERVER_READY_EVENT,
} from './model/embeddedServer'
import { isCapacitorNative, usesEmbeddedServer } from './model/serverConnection'
import { useBinaryThemeManager } from './model/theme'

const isNativeApp = isCapacitorNative()
const keepAliveViews = computed(() =>
  isNativeApp ? ['Player'] : ['Player', 'List', 'Settings', 'Download']
)
const warmedRoutes = new Set(['Home'])

const themeMgr = useBinaryThemeManager()
onBeforeMount(() => {
  themeMgr.setLightAlias('downtify-light')
  themeMgr.setDarkAlias('downtify-dark')
})

function routeTransitionName(route) {
  return warmedRoutes.has(route.name) ? 'page-fast' : 'page'
}

router.beforeEach((to, from) => {
  if (to.name === from.name) return true

  const instantKeepAlive =
    keepAliveViews.value.includes(String(to.name)) && warmedRoutes.has(to.name)
  if (!instantKeepAlive) beginAppLoading()
  return true
})

router.afterEach((to) => {
  warmedRoutes.add(to.name)
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      endAppLoading()
    })
  })
})

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
  window.setTimeout(preloadRouteComponents, 700)

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

<style>
.page-enter-active,
.page-leave-active,
.page-fast-enter-active,
.page-fast-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.page-fast-enter-active,
.page-fast-leave-active {
  transition-duration: 0.12s;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.page-fast-enter-from,
.page-fast-leave-to {
  opacity: 0;
  transform: none;
}
</style>
