import { createWebHistory, createRouter } from 'vue-router'
import Home from '/src/views/Front.vue'
import Search from '/src/views/Search.vue'
import Download from '/src/views/Download.vue'
import List from '/src/views/Downloads.vue'
import Monitor from '/src/views/Monitor.vue'
import Player from '/src/views/Player.vue'
import Health from '/src/views/Health.vue'
import Metadata from '/src/views/Metadata.vue'
import Settings from '/src/views/Settings.vue'
import config from '/src/config'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { mobileTitleKey: 'nav.home' },
  },
  {
    path: '/search/:query(.*)',
    name: 'SearchLegacy',
    component: Search,
    meta: { mobileTitleKey: 'nav.search' },
  },
  {
    path: '/search',
    name: 'Search',
    component: Search,
    meta: { mobileTitleKey: 'nav.search' },
  },
  {
    path: '/download',
    name: 'Download',
    component: Download,
    meta: { mobileTitleKey: 'nav.queue' },
  },
  {
    path: '/list',
    name: 'List',
    component: List,
    meta: { mobileTitleKey: 'nav.library' },
  },
  {
    path: '/monitor',
    name: 'Monitor',
    component: Monitor,
    meta: { mobileTitleKey: 'nav.monitor' },
  },
  {
    path: '/player',
    name: 'Player',
    component: Player,
    meta: { mobileTitleKey: 'nav.player' },
  },
  {
    path: '/health',
    name: 'Health',
    component: Health,
    meta: { mobileTitleKey: 'nav.health' },
  },
  {
    path: '/metadata',
    name: 'Metadata',
    component: Metadata,
    meta: { mobileTitleKey: 'nav.metadata' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { mobileTitleKey: 'nav.settings' },
  },
]

const router = createRouter({
  history: createWebHistory(config.BASEURL),
  routes,
})

export default router
