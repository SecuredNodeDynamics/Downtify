<template>
  <div class="min-h-0 overflow-x-hidden">
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
