<template>
  <div class="queue-view">
    <Navbar />
    <DownloadList />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import Navbar from '/src/components/Navbar.vue'
import DownloadList from '/src/components/DownloadList.vue'

onMounted(() => window.scroll(0, 0))
</script>

<style scoped>
.queue-view {
  @apply flex min-h-0 flex-col overflow-hidden;
  height: calc(
    100dvh - var(--app-header-height) - var(--app-safe-top) -
      var(--app-bottom-nav-height) - var(--app-safe-bottom)
  );
  max-height: calc(
    100dvh - var(--app-header-height) - var(--app-safe-top) -
      var(--app-bottom-nav-height) - var(--app-safe-bottom)
  );
}

@media (min-width: 1024px) {
  .queue-view {
    height: auto;
    max-height: none;
    overflow: visible;
  }
}
</style>
