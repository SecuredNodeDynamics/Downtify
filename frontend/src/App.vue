<template>
  <StarField />
  <div class="app-shell min-h-dvh flex flex-col text-base-content overflow-x-hidden">
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
    <Settings />
  </div>
</template>

<script setup>
import { onBeforeMount } from 'vue'
import BottomNav from './components/BottomNav.vue'
import Footer from './components/Footer.vue'
import MobileAppBar from './components/MobileAppBar.vue'
import MobileMoreSheet from './components/MobileMoreSheet.vue'
import MobileSearchSheet from './components/MobileSearchSheet.vue'
import Settings from './components/Settings.vue'
import StarField from './components/StarField.vue'
import { useBinaryThemeManager } from './model/theme'

const themeMgr = useBinaryThemeManager()
onBeforeMount(() => {
  themeMgr.setLightAlias('downtify-light')
  themeMgr.setDarkAlias('downtify-dark')
})
</script>

<style>
.page-enter-active,
.page-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease;
}
.page-enter-from,
.page-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
