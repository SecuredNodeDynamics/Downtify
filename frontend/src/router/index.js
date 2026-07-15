import { createWebHistory, createRouter } from 'vue-router'
import config from '/src/config'
import Home from '/src/views/Front.vue'
import Search from '/src/views/Search.vue'
import Download from '/src/views/Download.vue'
import List from '/src/views/Downloads.vue'
import Player from '/src/views/Player.vue'

const Monitor = () => import('/src/views/Monitor.vue')
const Health = () => import('/src/views/Health.vue')
const Metadata = () => import('/src/views/Metadata.vue')
const Settings = () => import('/src/views/Settings.vue')

const routePreloaders = [Monitor, Health, Settings]

export function preloadRouteComponents() {
  const preload = () => {
    for (const load of routePreloaders) {
      void load()
    }
  }
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    window.requestIdleCallback(preload, { timeout: 4000 })
    return
  }
  window.setTimeout(preload, 1200)
}

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
