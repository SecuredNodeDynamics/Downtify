<template>
  <StarField />
  <div
    class="app-shell flex min-h-dvh flex-col overflow-x-hidden text-base-content lg:min-h-dvh lg:overflow-visible"
  >
    <MobileAppBar />
    <main class="mobile-main flex-1 overflow-x-hidden">
      <router-view v-slot="{ Component, route }">
        <transition name="page" mode="out-in">
          <component :is="Component" :key="route.fullPath" />
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
import { onBeforeMount, onMounted } from 'vue'
import BottomNav from './components/BottomNav.vue'
import Footer from './components/Footer.vue'
import MobileAppBar from './components/MobileAppBar.vue'
import MobileMoreSheet from './components/MobileMoreSheet.vue'
import MobileSearchSheet from './components/MobileSearchSheet.vue'
import StarField from './components/StarField.vue'
import router from './router'
import { useBinaryThemeManager } from './model/theme'

const themeMgr = useBinaryThemeManager()
onBeforeMount(() => {
  themeMgr.setLightAlias('downtify-light')
  themeMgr.setDarkAlias('downtify-dark')
})

onMounted(async () => {
  const capacitor = window.Capacitor
  if (!capacitor?.isNativePlatform?.()) return
  try {
    const { App } = await import('@capacitor/app')
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
</script>

<style>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-enter-from,
.page-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
